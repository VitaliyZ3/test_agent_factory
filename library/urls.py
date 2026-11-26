from django.urls import path

from . import views

app_name = 'library'

urlpatterns = [
    path('', views.BookListView.as_view(), name='book_list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('books/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('loans/', views.my_loans, name='my_loans'),
    path('loans/<int:pk>/return/', views.return_book, name='return_book'),
]
