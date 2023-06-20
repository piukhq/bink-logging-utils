import logging
from collections.abc import Callable
from contextlib import suppress
from typing import TYPE_CHECKING, cast

from gunicorn.glogging import Logger
from loguru import logger

from bink_logging_utils.filters import GunicornAccessHealthzFilter

if TYPE_CHECKING:
    from gunicorn.config import Config


def loguru_intercept_handler_factory(
    add_extras: Callable[[logging.LogRecord], dict] | None = None
) -> type[logging.Handler]:
    """
    Factory for a loguru InterceptHandler.

    the optional add_extras function can be used to add new extras to the resulting loguru record or to override the
    two default extras: funnelled_record_path and x_azure_ref.

    NB:
    overriding funnelled_record_path can result in an exception in the default patcher set in `init_loguru_root_sink`

    """

    class NewInterceptHandler(logging.Handler):
        # Taken from loguru documentation:
        # https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
        def emit(self, record: logging.LogRecord) -> None:
            level: int | str
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                if frame.f_back:
                    frame = frame.f_back
                depth += 1

            extras: dict[str, str | dict[str, str | int]] = {
                "funnelled_record_path": {
                    "name": record.name,
                    "func": record.funcName,
                    "line": record.lineno,
                }
            }

            with suppress(KeyError, TypeError):
                # A gunicorn log record contains information in the following format
                # https://docs.gunicorn.org/en/stable/settings.html#access-log-format
                # i.e `X-Azure-Ref` request header is represented as `{x-azure-ref}i`
                extras |= {
                    "x_azure_ref": cast(str, record.args["{x-azure-ref}i"]),  # type: ignore [index,call-overload]
                }

            if add_extras:
                extras |= add_extras(record)

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage(), **extras)

    return NewInterceptHandler


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
