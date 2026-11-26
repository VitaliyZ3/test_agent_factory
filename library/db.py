from django.db.models import CharField, Func


def register_sqlite_functions(sender, connection, **kwargs):
    # SQLite's LOWER() and LIKE are case-insensitive only for ASCII,
    # so Cyrillic search needs a Python-backed lowercase function.
    if connection.vendor == 'sqlite':
        connection.connection.create_function(
            'py_lower', 1, lambda value: value.lower() if value is not None else None, deterministic=True
        )


class UnicodeLower(Func):
    function = 'LOWER'
    output_field = CharField()

    def as_sqlite(self, compiler, connection, **extra_context):
        return super().as_sql(compiler, connection, function='py_lower', **extra_context)
