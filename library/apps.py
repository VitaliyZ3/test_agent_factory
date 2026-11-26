from django.apps import AppConfig
from django.db.backends.signals import connection_created


class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library'
    verbose_name = 'Бібліотека'

    def ready(self):
        from .db import register_sqlite_functions

        connection_created.connect(register_sqlite_functions)
