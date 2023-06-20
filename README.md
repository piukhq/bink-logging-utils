# Bink Logging Utils

Helper functions to setup loguru as the output for all the loggers in a project.


The `init_loguru_root_sink` will initialise loguru default sink.

The two factories provide:
- A costum Gunicon Logger that funnels the output of gunicorn logs to loguru and, by default,
filters out any gunicorn.access request to the `/healthz`, `/livez`, `/readyz`, and `/metrics` endpoints.
- A generic InterecptHandler that can be set as the main Handler to any existing logging configuration to funnel it
into loguru.
