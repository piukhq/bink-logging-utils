import logging
from collections.abc import Callable
from contextlib import suppress
from typing import cast

from loguru import logger


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

            with logger.contextualize(**extras):
                logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    return NewInterceptHandler
