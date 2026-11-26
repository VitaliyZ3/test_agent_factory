from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

LOAN_PERIOD_DAYS = 14


class Author(models.Model):
    first_name = models.CharField('імʼя', max_length=100)
    last_name = models.CharField('прізвище', max_length=100)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'автор'
        verbose_name_plural = 'автори'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Genre(models.Model):
    name = models.CharField('назва', max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'жанр'
        verbose_name_plural = 'жанри'

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField('назва', max_length=200)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='books', verbose_name='автор')
    genres = models.ManyToManyField(Genre, blank=True, related_name='books', verbose_name='жанри')
    isbn = models.CharField('ISBN', max_length=13, unique=True)
    published_year = models.PositiveIntegerField('рік видання', null=True, blank=True)
    description = models.TextField('опис', blank=True)
    total_copies = models.PositiveIntegerField('кількість примірників', default=1)

    class Meta:
        ordering = ['title']
        verbose_name = 'книга'
        verbose_name_plural = 'книги'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('library:book_detail', args=[self.pk])

    @property
    def available_copies(self):
        return self.total_copies - self.loans.filter(returned_at__isnull=True).count()

    @property
    def is_available(self):
        return self.available_copies > 0


class LoanQuerySet(models.QuerySet):
    def active(self):
        return self.filter(returned_at__isnull=True)

    def overdue(self):
        return self.active().filter(due_date__lt=timezone.localdate())


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans', verbose_name='книга')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans', verbose_name='читач'
    )
    borrowed_at = models.DateTimeField('видано', auto_now_add=True)
    due_date = models.DateField('повернути до')
    returned_at = models.DateTimeField('повернено', null=True, blank=True)

    objects = LoanQuerySet.as_manager()

    class Meta:
        ordering = ['-borrowed_at']
        verbose_name = 'видача'
        verbose_name_plural = 'видачі'

    def __str__(self):
        return f'{self.book} → {self.user}'

    @classmethod
    def borrow(cls, book, user):
        if not book.is_available:
            raise ValidationError('Немає вільних примірників цієї книги.')
        if cls.objects.active().filter(book=book, user=user).exists():
            raise ValidationError('Ви вже взяли цю книгу.')
        return cls.objects.create(
            book=book, user=user, due_date=timezone.localdate() + timedelta(days=LOAN_PERIOD_DAYS)
        )

    def mark_returned(self):
        if self.returned_at is not None:
            raise ValidationError('Книгу вже повернено.')
        self.returned_at = timezone.now()
        self.save(update_fields=['returned_at'])

    @property
    def is_overdue(self):
        return self.returned_at is None and self.due_date < timezone.localdate()
