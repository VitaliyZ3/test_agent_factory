from itertools import count

from django.contrib.auth import get_user_model

from library.models import Author, Book, Genre

_seq = count(1)


def make_user(username=None, password='pass12345'):
    return get_user_model().objects.create_user(username=username or f'user{next(_seq)}', password=password)


def make_author(**kwargs):
    kwargs.setdefault('first_name', 'Тарас')
    kwargs.setdefault('last_name', 'Шевченко')
    return Author.objects.create(**kwargs)


def make_book(**kwargs):
    genres = kwargs.pop('genres', [])
    kwargs.setdefault('title', 'Кобзар')
    kwargs.setdefault('author', make_author())
    kwargs.setdefault('isbn', f'978{next(_seq):010d}')
    book = Book.objects.create(**kwargs)
    book.genres.set(genres)
    return book


def make_genre(name='Поезія'):
    return Genre.objects.create(name=name)
