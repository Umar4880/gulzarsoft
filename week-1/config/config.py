import logging
import logging.config
import logging.handlers
from pathlib import Path
import yaml
from queue import Queue
import atexit
from collections.abc import Iterator

log_queue = Queue(-1)

_queue_listener = None


def _iter_all_handlers() -> Iterator[logging.Handler]:
    """Yield all known handlers, including non-root handlers created by dictConfig."""
    seen: set[int] = set()

    for handler in logging.getLogger().handlers:
        if id(handler) not in seen:
            seen.add(id(handler))
            yield handler

    # dictConfig can create handlers that are not attached to root (e.g. file/console
    # when root has only QueueHandler). They still exist in logging internals.
    for ref in getattr(logging, "_handlerList", []):
        handler = ref()
        if handler is not None and id(handler) not in seen:
            seen.add(id(handler))
            yield handler

def setup_logging() -> None:
    global _queue_listener

    # Avoid duplicate listeners/handlers if setup is called more than once.
    if _queue_listener is not None:
        return

    cfg_path = Path(__file__).with_name("log-config.yaml")
    project_root = cfg_path.parent.parent
    (project_root / "log").mkdir(parents=True, exist_ok=True)

    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    logging.config.dictConfig(cfg)

    handlers = list(_iter_all_handlers())
    file_handler = next(
        (h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)),
        None,
    )
    console_handler = next(
        (
            h
            for h in handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.handlers.RotatingFileHandler)
        ),
        None,
    )

    if file_handler is None or console_handler is None:
        raise RuntimeError(
            "Logging handlers not found. Ensure 'file' and 'console' handlers are defined in log-config.yaml"
        )

    _queue_listener = logging.handlers.QueueListener(
        log_queue,
        file_handler,
        console_handler,
        respect_handler_level=True,
    )

    
    _queue_listener.start()
    atexit.register(_queue_listener.stop)