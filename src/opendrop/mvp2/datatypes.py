from enum import Enum


class ViewPresenterState(Enum):
    INITIALISING = 0
    INITIALISED = 1
    SETTING_UP = 2
    UP = 3
    TEARING_DOWN = 4
    DOWN = 5
