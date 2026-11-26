from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .db import UnicodeLower
from .models import Book, Genre, Loan


class BookListView(ListView):
    model = Book
    paginate_by = 10

    def get_queryset(self):
        qs = Book.objects.select_related('author').prefetch_related('genres')
        query = self.request.GET.get('q', '').strip().lower()
        if query:
            qs = qs.annotate(
                title_lower=UnicodeLower('title'),
                first_name_lower=UnicodeLower('author__first_name'),
                last_name_lower=UnicodeLower('author__last_name'),
            ).filter(
                Q(title_lower__contains=query)
                | Q(first_name_lower__contains=query)
                | Q(last_name_lower__contains=query)
                | Q(isbn__contains=query)
            )
        genre = self.request.GET.get('genre')
        if genre:
            qs = qs.filter(genres__pk=genre)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['genres'] = Genre.objects.all()
        context['selected_genre'] = self.request.GET.get('genre', '')
        return context


class BookDetailView(DetailView):
    model = Book

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user_loan'] = (
            Loan.objects.active().filter(book=self.object, user=user).first()
            if user.is_authenticated
            else None
        )
        return context


@login_required
@require_POST
def borrow_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    try:
        loan = Loan.borrow(book, request.user)
    except ValidationError as e:
        messages.error(request, e.messages[0])
    else:
        messages.success(request, f'Ви взяли «{book}». Поверніть до {loan.due_date:%d.%m.%Y}.')
    return redirect(book)


@login_required
@require_POST
def return_book(request, pk):
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    try:
        loan.mark_returned()
    except ValidationError as e:
        messages.error(request, e.messages[0])
    else:
        messages.success(request, f'Книгу «{loan.book}» повернено.')
    return redirect('library:my_loans')


@login_required
def my_loans(request):
    loans = Loan.objects.filter(user=request.user).select_related('book', 'book__author')
    return render(request, 'library/my_loans.html', {
        'active_loans': [loan for loan in loans if loan.returned_at is None],
        'past_loans': [loan for loan in loans if loan.returned_at is not None],
    })
