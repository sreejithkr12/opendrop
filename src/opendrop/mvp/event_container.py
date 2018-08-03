from enum import IntEnum, Enum
from typing import Optional


class MouseMoveEvent:
    # Timestamp of the event
    timestamp = None  # type: Optional[float]

    # Position of the cursor
    pos = None  # type: Optional[Tuple[int, int]]

    # Modifier bitfield
    state = None  # type: Optional[ModifierType]

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MouseButtonEvent:
    # Timestamp of the event
    timestamp = None  # type: Optional[float]

    # Type of event (single click, double click, press/release)
    action = None  # type: Optional[MouseActionType]

    # Button acted upon
    button = None  # type: Optional[MouseButtonType]

    # Position of the cursor
    pos = None  # type: Optional[Tuple[int, int]]

    # Modifier bitfield
    state = None  # type: Optional[ModifierType]

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ModifierType(IntEnum):
    SHIFT = 1
    CAPSLOCK = 2
    CONTROL = 4
    ALT = 8
    BUTTON1 = 16
    BUTTON2 = 32
    BUTTON3 = 64


class MouseActionType(Enum):
    PRESS = 1
    RELEASE = 2
    DOUBLE_CLICK = 3
    TRIPLE_CLICK = 4


class MouseButtonType(Enum):
    L_BUTTON = 1
    M_BUTTON = 2
    R_BUTTON = 3


class KeyCode(Enum):
    UNKNOWN = 1
    ESC = 2
    r = 3
    R = 4, r
    n = 5
    N = 6, n

    def __init__(self, val: int, lower_val: Optional[int] = None):
        self.val = val  # type: int
        self._lower = type(self)(lower_val) if lower_val is not None else None  # type: Optional[KeyCode]

    def lower(self) -> 'KeyCode':
        return self._lower if self._lower else self
