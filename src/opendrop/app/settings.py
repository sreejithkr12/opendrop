from pathlib import Path
from typing import Union, Optional, MutableMapping

from opendrop.utility import persistentdata


class CameraCaptureHistorySettings:
    def __init__(self, data: MutableMapping):
        self._data = data

    @property
    def enabled(self) -> bool:
        if not self._enabled or not self.location.exists():
            return False

        return self._enabled

    @property
    def _enabled(self) -> bool:
        return self._data['enabled']

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._data['enabled'] = value

    @property
    def location(self) -> Optional[Path]:
        key = 'location'

        if self._data[key] is None:
            return None

        return Path(self._data[key]).expanduser().absolute()

    @location.setter
    def location(self, value: Optional[Union[Path, str]]) -> None:
        self._data['location'] = str(value) if value is not None else None

    @property
    def limit(self) -> int:
        return self._data['limit']

    @limit.setter
    def limit(self, value: int) -> None:
        self._data['limit'] = value


class Settings:
    def __init__(self, data: MutableMapping):
        self._data = data
        self._camera_capture_history = CameraCaptureHistorySettings(data['camera_capture_history'])

    @property
    def camera_capture_history(self) -> CameraCaptureHistorySettings:
        return self._camera_capture_history

    @property
    def default_drop_save_parent_directory(self) -> Optional[Path]:
        key = 'default_drop_save_parent_directory'

        if self._data[key] is None:
            return None

        return Path(self._data[key]).expanduser().absolute()

    @default_drop_save_parent_directory.setter
    def default_drop_save_parent_directory(self, value: Optional[Union[Path, str]]) -> None:
        self._data['default_drop_save_parent_directory'] = str(value) if value is not None else None

    @property
    def gravity(self) -> float:
        return self._data['gravity']

    @gravity.setter
    def gravity(self, value: float) -> None:
        self._data['gravity'] = value


settings = Settings(persistentdata.open(Path(__file__).parent/'settings.json'))
