from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from library.models import LOAN_PERIOD_DAYS, Loan

from .factories import make_author, make_book, make_user


class BookModelTests(TestCase):
    def test_str_and_absolute_url(self):
        book = make_book(title='Лісова пісня')
        self.assertEqual(str(book), 'Лісова пісня')
        self.assertEqual(book.get_absolute_url(), f'/books/{book.pk}/')

    def test_isbn_is_unique(self):
        make_book(isbn='9780000000001')
        with self.assertRaises(IntegrityError):
            make_book(isbn='9780000000001')

    def test_available_copies_ignores_returned_loans(self):
        book = make_book(total_copies=2)
        Loan.borrow(book, make_user()).mark_returned()
        Loan.borrow(book, make_user())
        self.assertEqual(book.available_copies, 1)
        self.assertTrue(book.is_available)


class AuthorModelTests(TestCase):
    def test_str(self):
        self.assertEqual(str(make_author(first_name='Леся', last_name='Українка')), 'Леся Українка')


class LoanModelTests(TestCase):
    def setUp(self):
        self.book = make_book(total_copies=1)
        self.user = make_user()

    def test_borrow_sets_due_date(self):
        loan = Loan.borrow(self.book, self.user)
        self.assertEqual(loan.due_date, timezone.localdate() + timedelta(days=LOAN_PERIOD_DAYS))
        self.assertIsNone(loan.returned_at)
        self.assertFalse(self.book.is_available)

    def test_cannot_borrow_when_no_copies_left(self):
        Loan.borrow(self.book, self.user)
        with self.assertRaisesMessage(ValidationError, 'Немає вільних примірників'):
            Loan.borrow(self.book, make_user())

    def test_cannot_borrow_same_book_twice(self):
        self.book.total_copies = 2
        self.book.save()
        Loan.borrow(self.book, self.user)
        with self.assertRaisesMessage(ValidationError, 'вже взяли'):
            Loan.borrow(self.book, self.user)

    def test_mark_returned_frees_copy(self):
        loan = Loan.borrow(self.book, self.user)
        loan.mark_returned()
        self.assertIsNotNone(loan.returned_at)
        self.assertTrue(self.book.is_available)

    def test_cannot_return_twice(self):
        loan = Loan.borrow(self.book, self.user)
        loan.mark_returned()
        with self.assertRaises(ValidationError):
            loan.mark_returned()

    def test_overdue(self):
        loan = Loan.borrow(self.book, self.user)
        self.assertFalse(loan.is_overdue)
        loan.due_date = timezone.localdate() - timedelta(days=1)
        loan.save()
        self.assertTrue(loan.is_overdue)
        self.assertQuerySetEqual(Loan.objects.overdue(), [loan])
        loan.mark_returned()
        self.assertFalse(loan.is_overdue)
        self.assertFalse(Loan.objects.overdue().exists())
