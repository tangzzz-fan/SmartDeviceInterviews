"""T6-Q4 JSON 结构化日志：logging + JSONFormatter（替换 print）"""
import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """每行一条 JSON——字段可被 ELK/Loki 直接消费"""

    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)     # 业务字段走 extra
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:                              # 防重复挂 handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_with(logger, level, msg, **fields):
    """附带结构化字段的便捷入口"""
    record = logger.makeRecord(logger.name, level, "", 0, msg, (), None)
    record.extra_fields = fields
    logger.handle(record)
