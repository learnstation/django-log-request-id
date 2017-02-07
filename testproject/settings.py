from django.conf import global_settings

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

DEBUG = True

SECRET_KEY = 'secret'

ROOT_URLCONF = "testproject.urls"

INSTALLED_APPS = ["log_request_id"]

MIDDLEWARE_CLASSES = [
    'log_request_id.middleware.RequestIDMiddleware',
    # ... other middleware goes here
] + list(global_settings.MIDDLEWARE_CLASSES)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'log_request_id.filters.RequestIDFilter'
        },
        'unix_time': {
            '()': 'log_request_id.filters.UnixTimeFilter'
        },
        'request_order_number': {
            '()': 'log_request_id.filters.RequestOrderNumberFilter'
        }
    },
    'formatters': {
        'standard': {
            'format': '%(levelname)-8s [%(asctime)s] [%(unix_time)s] [%(request_order_number)s] [%(request_id)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'request_id_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filters': ['request_id', 'unix_time', 'request_order_number'],
            'formatter': 'standard',
            'filename': "/tmp/request_id.log",
            'encoding': 'utf-8'
        },
    },
    'loggers': {
        'log_request_id.middleware': {
            'handlers': ['request_id_handler'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
