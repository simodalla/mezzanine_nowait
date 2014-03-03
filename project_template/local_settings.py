
DEBUG = True

# Make these unique, and don't share it with anybody.
SECRET_KEY = "%(SECRET_KEY)s"
NEVERCACHE_KEY = "%(NEVERCACHE_KEY)s"

# DATABASES = {
#     "default": {
#         # Ends with "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
#         "ENGINE": "django.db.backends.sqlite3",
#         # DB name or path to database file if using sqlite3.
#         "NAME": "dev.db",
#         # Not used with sqlite3.
#         "USER": "",
#         # Not used with sqlite3.
#         "PASSWORD": "",
#         # Set to empty string for localhost. Not used with sqlite3.
#         "HOST": "",
#         # Set to empty string for default. Not used with sqlite3.
#         "PORT": "",
#     }
# }

DATABASES = {
    "default": {
        # Add "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        # DB name or path to database file if using sqlite3.
        "NAME": "mezzanine_nowait",
        # Not used with sqlite3.
        "USER": "",
        # Not used with sqlite3.
        "PASSWORD": "",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "localhost",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}

from django import get_version
if int(get_version().split('.')[1]) <= 5:
    TEST_RUNNER = 'discover_runner.DiscoverRunner'
    TEST_DISCOVER_PATTERN = "test_*.py"
else:
    TEST_RUNNER = 'django.test.runner.DiscoverRunner'

