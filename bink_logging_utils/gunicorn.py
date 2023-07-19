import logging
import sys
from typing import TYPE_CHECKING

from bink_logging_utils.filters import GunicornAccessHealthzFilter
from bink_logging_utils.handlers import loguru_intercept_handler_factory

try:
    from gunicorn.glogging import Logger

    if TYPE_CHECKING:
        from gunicorn.config import Config

except ImportError:
    sys.exit("Gunicorn extra not installed.")


def gunicorn_logger_factory(
    *,
    intercept_handler_class: type[logging.Handler] | None = None,
    access_log_level: int | str | None = None,
    error_log_level: int | str | None = None,
    access_log_filters: list[type[logging.Filter]] | None = None,
    error_log_filters: list[type[logging.Filter]] | None = None,
) -> Logger:
    """
    Factory for a custom Guncorn Logger that funnels gunicorn logs output to loguru via InterceptHandler

    intercept_handler_class will default to `loguru_intercept_handler_factory()` if not provided.

    access_log_filters will default to `[GunicornAccessHealthzFilter]` if not provided.

    error_log_filters will default to `[]` if not provided.
    """

    if not intercept_handler_class:
        intercept_handler = loguru_intercept_handler_factory()()
    else:
        intercept_handler = intercept_handler_class()

    class NewGunicornLogger(Logger):
        def setup(self, cfg: "Config") -> None:
            super().setup(cfg)
            self.error_log.handlers = [intercept_handler]
            if error_log_level:
                self.error_log.level = error_log_level

            self.access_log.handlers = [intercept_handler]
            if access_log_level:
                self.access_log.level = access_log_level

            for access_filter in access_log_filters or [GunicornAccessHealthzFilter]:
                self.access_log.addFilter(access_filter())

            for error_filter in error_log_filters or []:
                self.error_log.addFilter(error_filter())

    return NewGunicornLogger
