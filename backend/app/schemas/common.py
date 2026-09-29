from enum import StrEnum


class AssetType(StrEnum):
    DATASET = "DATASET"
    MODEL = "MODEL"


class RunState(StrEnum):
    CONFIGURED = "CONFIGURED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NOT_RUN = "NOT_RUN"


class FindingSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class FindingStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    NOT_RUN = "NOT_RUN"


class AssuranceStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
