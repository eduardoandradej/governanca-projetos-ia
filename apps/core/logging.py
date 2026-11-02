import logging

from . import context


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = context._correlation_id.get() or "-"
        return True
