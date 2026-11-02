from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)
APP_ENVIRONMENT_LABEL = env("APP_ENVIRONMENT_LABEL", default="Desenvolvimento")
