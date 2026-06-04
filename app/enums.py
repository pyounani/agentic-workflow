import enum


class LanternStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
