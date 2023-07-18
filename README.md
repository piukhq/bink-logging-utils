# Bink Logging Utils

Helper functions to setup loguru as the output for all the loggers in a project.

## using loguru directly
From the `bink_logging_utils` module import `init_loguru_root_sink`.

Calling this will initialise the default loguru sink.

**eg**
```python
from bink_logging_utils import init_loguru_root_sink

# ------- env vars -------- #
JSON_LOGGING: bool = ...
ROOT_LOG_LEVEL: str | int = ...
# ------------------------- #

init_loguru_root_sink(json_logging=JSON_LOGGING, sink_log_level=ROOT_LOG_LEVEL, show_pid=True)

```

## funnelling existing logging calls into loguru
From the `bink_logging_utils.handlers` module import `loguru_intercept_handler_factory`.

This function will return an `InterecptHandler` class that can be set as the default logging handler, this will let loguru handle all logs output.

**eg**
```python
import logging

from bink_logging_utils.handlers import loguru_intercept_handler_factory


InterceptHandler = loguru_intercept_handler_factory()

# then

logging.basicConfig(handlers=[InterceptHandler()], ...)

# or

logging.config.dictConfig(
    {
        ...
        "handlers": {
            "console": {"()": "path.to.InterceptHandler"},
        },
        ...
    }
)
```

## gunicorn
when installing this library specify the `gunicorn` extra **eg:** `poetry add bink-logging-utils[gunicorn]`

From the `bink_logging_utils.gunicorn` module import `gunicorn_logger_factory`.

This function will return a custom Glogger class that funnels the output of gunicorn logs into loguru and, by default,
filters out any gunicorn.access requests to the `/healthz`, `/livez`, `/readyz`, and `/metrics` endpoints.

Update the Dockerfile gunicorn run command with the flag `--logger-class=path.to.CustomGunicornLogger`.

**eg**

pyproject.toml
```toml
[[tool.poetry.source]]
name = "bink-pypi"
url = "https://pypi.gb.bink.com/simple"
default = false
secondary = false

[tool.poetry.dependencies]
...
bink-logging-utils = {version = "^1.1.0", source = "bink-pypi", extras=["gunicorn"]}
...
```

python module
```python
from bink_logging_utils.handlers import loguru_intercept_handler_factory
from bink_logging_utils.gunicorn import gunicorn_logger_factory


InterceptHandler = loguru_intercept_handler_factory()

CustomGunicornLogger = gunicorn_logger_factory(intercept_handler_class=InterceptHandler)
```

Dockerfile
```docker
...

CMD [ "gunicorn", "--workers=2", "--error-logfile=-", "--access-logfile=-", \
        "--bind=0.0.0.0:9000", "--logger-class=path.to.CustomGunicornLogger", \
        "app.wsgi" ]
```
