"""
Structured JSON logging formatter for production.

Container log aggregators (Datadog, Loki, CloudWatch) consume JSON far more
reliably than free text. This formatter emits one log line per record as JSON
with the fields that matter for tracing and alerting.
"""

import json
import logging


class JsonFormatter(logging.Formatter):
    """Render a LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id  # type: ignore[attr-defined]
        return json.dumps(payload, default=str)
