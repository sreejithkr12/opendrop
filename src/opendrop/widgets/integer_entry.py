from typing import Optional

from gi.repository import GObject

from opendrop.widgets.validated_entry import ValidatedEntry


class IntegerEntry(ValidatedEntry):
    _min = None  # type: Optional[int]
    _max = None  # type: Optional[int]
    _default = None  # type: Optional[int]

    @GObject.Property
    def min(self) -> Optional[int]:
        return self._min

    @min.setter
    def min(self, value: Optional[int]) -> None:
        self._min = value

    @GObject.Property
    def max(self) -> Optional[int]:
        return self._max

    @max.setter
    def max(self, value: Optional[int]) -> None:
        self._max = value

    @GObject.Property
    def default(self) -> Optional[int]:
        return self._default

    @default.setter
    def default(self, value: Optional[int]) -> None:
        self._default = value

    def restrict(self, value: Optional[int]) -> Optional[int]:
        if value is None:
            if self.default is not None:
                return self.restrict(self.default)

            return None

        if self.min is not None:
            value = max(value, self.min)

        if self.max is not None:
            value = min(value, self.max)

        return value

    def validate(self, text: str) -> bool:
        if '+' in text and self.max is not None and self.max < 0:
            return False
        elif '-' in text and self.min is not None and self.min >= 0:
            return False

        try:
            self.t_from_str(text)
            return True
        except (TypeError, ValueError):
            if text in ('+', '-'):
                return True

            return False

    def t_from_str(self, text: str) -> Optional[int]:
        if text == '':
            return None
        elif text in ('+', '-'):
            return None

        return int(text)

    def str_from_t(self, value: Optional[int]) -> str:
        if value is None:
            return ''

        return str(int(value))
