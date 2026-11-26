# Бібліотека (Django)

Простий сайт бібліотеки: каталог книг з пошуком і фільтром за жанром, видача та повернення книг, сторінка «Мої книги», адмінка для бібліотекаря.

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Книги, авторів і жанри додавайте через `/admin/`.

## Тести

```bash
python manage.py test
```

CI (GitHub Actions, `.github/workflows/tests.yml`) запускає тести на кожен pull request і push у `main`.
