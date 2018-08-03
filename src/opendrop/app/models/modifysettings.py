from pathlib import Path
from typing import Mapping, Any

from opendrop.app.settings import Settings
from opendrop.mvp.Model import Model
from opendrop.utility import data_binding


class ModifySettings(Model):
    def __init__(self, settings_data: Settings):
        super().__init__()

        self._settings_data = settings_data  # type: Settings

        self._default_drop_save_parent_directory = self._settings_data.default_drop_save_parent_directory  # type: Path

        self._camera_history_enabled = self._settings_data.camera_capture_history.enabled  # type: bool
        self._camera_history_location = self._settings_data.camera_capture_history.location  # type: Path
        self._camera_history_limit = self._settings_data.camera_capture_history.limit  # type: int

        self._gravity = self._settings_data.gravity  # type: float

    @data_binding.property
    def default_drop_save_parent_directory(self) -> str:
        return str(self._default_drop_save_parent_directory)

    @default_drop_save_parent_directory.setter
    def default_drop_save_parent_directory(self, value: str) -> None:
        self._default_drop_save_parent_directory = Path(value)

    @data_binding.property
    def camera_history_enabled(self) -> bool:
        if self._camera_history_enabled and not self._camera_history_location.exists():
            return False

        return self._camera_history_enabled

    @camera_history_enabled.setter
    def camera_history_enabled(self, value: bool) -> None:
        self._camera_history_enabled = value

    @data_binding.property
    def camera_history_location(self) -> str:
        return str(self._camera_history_location)

    @camera_history_location.setter
    def camera_history_location(self, value: str) -> None:
        self._camera_history_location = Path(value) if value is not None else None

    @data_binding.property
    def camera_history_limit(self) -> int:
        return self._camera_history_limit

    @camera_history_limit.setter
    def camera_history_limit(self, value: int) -> None:
        self._camera_history_limit = value

    @data_binding.property
    def gravity(self) -> float:
        return self._gravity

    @gravity.setter
    def gravity(self, value: float) -> None:
        self._gravity = value

    def validate(self) -> Mapping[str, Any]:
        pass

    def save(self) -> None:
        assert not self.validate()

        self._settings_data.default_drop_save_parent_directory = self.default_drop_save_parent_directory

        self._settings_data.camera_capture_history.enabled = self.camera_history_enabled
        self._settings_data.camera_capture_history.location = self.camera_history_location
        self._settings_data.camera_capture_history.limit = self.camera_history_limit
        self._settings_data.gravity = self.gravity
