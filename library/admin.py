from django.contrib import admin

from .models import Author, Book, Genre, Loan


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'published_year', 'total_copies']
    list_filter = ['genres']
    search_fields = ['title', 'isbn', 'author__last_name']
    filter_horizontal = ['genres']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'borrowed_at', 'due_date', 'returned_at']
    list_filter = ['returned_at']
    raw_id_fields = ['book', 'user']
