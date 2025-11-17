import logging
import traceback

log = logging.getLogger(__name__)


def log_info(err: Exception) -> None:
    log.info(f"Handled exception: {type(err).__name__} — {err}")


def log_error(err: Exception) -> None:
    stack = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    log.error("Handled exception: %s — %s\n%s", type(err).__name__, err, stack)
