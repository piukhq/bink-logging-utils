import logging
from typing import cast


class GunicornAccessHealthzFilter(logging.Filter):
    """Filter out requests to `/healthz`, `/livez`, `/readyz`, and `/metrics` endpoints"""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if (request_info := cast(str, record.args.get("r"))) and [  # type: ignore [union-attr]
            endpoint for endpoint in ("/healthz", "/livez", "/readyz", "/metrics") if endpoint in request_info
        ]:
            return False

        return True
