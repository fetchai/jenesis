from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, Optional

class TaskStatus(Enum):
    IDLE = 0
    IN_PROGRESS = 1
    COMPLETE = 2
    FAILED = 3


class Task(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def status(self) -> TaskStatus:
        pass

    @property
    @abstractmethod
    def status_text(self) -> str:
        pass

    @property
    def is_idle(self) -> bool:
        return self.status == TaskStatus.IDLE

    @property
    def is_in_progress(self) -> bool:
        return self.status == TaskStatus.IN_PROGRESS

    @property
    def is_complete(self) -> bool:
        return self.status == TaskStatus.COMPLETE

    @property
    def is_failed(self) -> bool:
        return self.status == TaskStatus.FAILED

    @property
    def is_done(self) -> bool:
        return self.is_complete or self.is_failed

    @abstractmethod
    def poll(self):
        pass
