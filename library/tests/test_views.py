from django.test import TestCase
from django.urls import reverse

from library.models import Loan

from .factories import make_author, make_book, make_genre, make_user


class BookListViewTests(TestCase):
    def test_lists_books(self):
        make_book(title='Кобзар')
        response = self.client.get(reverse('library:book_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Кобзар')

    def test_empty_catalog(self):
        response = self.client.get(reverse('library:book_list'))
        self.assertContains(response, 'Книг не знайдено')

    def test_search_by_title_and_author(self):
        make_book(title='Кобзар')
        make_book(title='Лісова пісня', author=make_author(first_name='Леся', last_name='Українка'))
        response = self.client.get(reverse('library:book_list'), {'q': 'українка'})
        self.assertContains(response, 'Лісова пісня')
        self.assertNotContains(response, 'Кобзар')

    def test_filter_by_genre(self):
        poetry, drama = make_genre('Поезія'), make_genre('Драма')
        make_book(title='Кобзар', genres=[poetry])
        make_book(title='Наталка Полтавка', genres=[drama])
        response = self.client.get(reverse('library:book_list'), {'genre': drama.pk})
        self.assertContains(response, 'Наталка Полтавка')
        self.assertNotContains(response, 'Кобзар')

    def test_pagination(self):
        author = make_author()
        for i in range(12):
            make_book(title=f'Книга {i:02d}', author=author)
        response = self.client.get(reverse('library:book_list'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['book_list']), 10)


class BookDetailViewTests(TestCase):
    def test_shows_book(self):
        book = make_book(title='Кобзар', isbn='9781234567890')
        response = self.client.get(book.get_absolute_url())
        self.assertContains(response, '9781234567890')
        self.assertContains(response, 'Увійдіть')

    def test_404_for_missing_book(self):
        response = self.client.get(reverse('library:book_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_shows_borrow_button_for_logged_in_user(self):
        book = make_book()
        self.client.force_login(make_user())
        response = self.client.get(book.get_absolute_url())
        self.assertContains(response, 'Взяти книгу')


class BorrowReturnViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.book = make_book(total_copies=1)

    def test_borrow_requires_login(self):
        url = reverse('library:borrow_book', args=[self.book.pk])
        response = self.client.post(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")
        self.assertFalse(Loan.objects.exists())

    def test_borrow_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('library:borrow_book', args=[self.book.pk]))
        self.assertEqual(response.status_code, 405)

    def test_borrow_creates_loan(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('library:borrow_book', args=[self.book.pk]), follow=True)
        self.assertRedirects(response, self.book.get_absolute_url())
        self.assertContains(response, 'Ви взяли')
        self.assertTrue(Loan.objects.active().filter(book=self.book, user=self.user).exists())

    def test_borrow_unavailable_book_shows_error(self):
        Loan.borrow(self.book, make_user())
        self.client.force_login(self.user)
        response = self.client.post(reverse('library:borrow_book', args=[self.book.pk]), follow=True)
        self.assertContains(response, 'Немає вільних примірників')
        self.assertFalse(Loan.objects.filter(user=self.user).exists())

    def test_return_book(self):
        loan = Loan.borrow(self.book, self.user)
        self.client.force_login(self.user)
        response = self.client.post(reverse('library:return_book', args=[loan.pk]), follow=True)
        self.assertRedirects(response, reverse('library:my_loans'))
        loan.refresh_from_db()
        self.assertIsNotNone(loan.returned_at)

    def test_cannot_return_someone_elses_loan(self):
        loan = Loan.borrow(self.book, make_user())
        self.client.force_login(self.user)
        response = self.client.post(reverse('library:return_book', args=[loan.pk]))
        self.assertEqual(response.status_code, 404)
        loan.refresh_from_db()
        self.assertIsNone(loan.returned_at)


class MyLoansViewTests(TestCase):
    def test_requires_login(self):
        response = self.client.get(reverse('library:my_loans'))
        self.assertEqual(response.status_code, 302)

    def test_shows_only_own_loans(self):
        user = make_user()
        Loan.borrow(make_book(title='Моя книга'), user)
        Loan.borrow(make_book(title='Чужа книга'), make_user())
        self.client.force_login(user)
        response = self.client.get(reverse('library:my_loans'))
        self.assertContains(response, 'Моя книга')
        self.assertNotContains(response, 'Чужа книга')


class AuthTests(TestCase):
    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_and_logout(self):
        make_user(username='reader', password='pass12345')
        response = self.client.post(reverse('login'), {'username': 'reader', 'password': 'pass12345'})
        self.assertRedirects(response, reverse('library:book_list'))
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('library:book_list'))
