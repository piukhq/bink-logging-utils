import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import FilterDict, FilterFunction, FormatFunction, PatcherFunction, Record


def init_loguru_root_sink(  # noqa: PLR0913
    *,
    json_logging: bool,
    sink_log_level: int | str,
    show_pid: bool,
    log_filter: "str | FilterDict | FilterFunction | None" = None,
    custom_patcher: "PatcherFunction | None" = None,
    custom_formatter: "str | FormatFunction | None" = None,
) -> None:
    """
    Initialise Loguru sink.

    json_logging: if True loguru will serialise the logs
    sink_log_level: anything below the provided level will not be outputted
    show_pid: adds pid `| <yellow>pid: {process}</yellow> |` to the default format
    log_filter: add log filters to the default sink
    custom_patcher: custom patcher to run after the default funnelled_record_path handling
    custom_formatter: string or function that overrides the default log format
    """

    class LoguruSinkPatcher:
        def __init__(self, extra_patcher: "PatcherFunction | None") -> None:
            self.extra_patcher = extra_patcher

        def __call__(self, record: "Record") -> None:
            if funnelled_record_path := record["extra"].pop("funnelled_record_path", None):
                record["name"] = funnelled_record_path["name"]
                record["function"] = funnelled_record_path["func"]
                record["line"] = funnelled_record_path["line"]

            if self.extra_patcher:
                self.extra_patcher(record)

    default_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    if show_pid:
        time, rest = default_format.split("|", 1)
        default_format = time + "| <yellow>pid: {process}</yellow> |" + rest

    logger.remove(0)
    logger.add(
        sink=sys.stderr,
        serialize=json_logging,
        colorize=not json_logging,
        format=custom_formatter or default_format,
        level=sink_log_level,
        filter=log_filter,
    )
    logger.configure(patcher=LoguruSinkPatcher(custom_patcher))
