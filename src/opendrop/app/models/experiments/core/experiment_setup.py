from abc import abstractmethod
from typing import Optional, List, Tuple, NewType, MutableMapping, Any

from opendrop import observer
from opendrop.image_filter.image_filter_group import ImageFilterGroup

from opendrop.mvp.Model import Model

from opendrop.observer.bases import Observer, ObserverType
from opendrop.observer.service import ObserverService
from opendrop.utility import data_binding

PointFloat2D = NewType('PointFloat2D', Tuple[float, float])
RectFloat = NewType('RectFloat', Tuple[PointFloat2D, PointFloat2D])

observer_service = ObserverService()  # type: ObserverService


class ChangeObserverRequest(Model):
    def __init__(self, parent: 'ExperimentSetup'):
        super().__init__()

        self._parent = parent  # type: ExperimentSetup

        self.type = None  # type: Optional[ObserverType]
        self.opts = {}

    def submit(self) -> None:
        self._parent.observer = observer_service.new_observer_by_type(self.type, **self.opts)


class ExperimentSetup(Model):
    observer_types = observer.types  # type: observer.types

    def __init__(self):
        super().__init__()

        self._observer = None  # type: Optional[Observer]
        self._frame_timestamps = [0]  # type: List[float]

        self.postproc = ImageFilterGroup()  # type: ImageFilterGroup

    def change_observer(self) -> ChangeObserverRequest:
        return ChangeObserverRequest(parent=self)

    @abstractmethod
    def start_experiment(self) -> None: pass

    @abstractmethod
    def validate(self) -> MutableMapping[str, Any]: pass

    @data_binding.property
    def frame_timestamps(self) -> List[float]:
        return self._frame_timestamps

    @frame_timestamps.setter
    def frame_timestamps(self, value: List[float]) -> None:
        self._frame_timestamps = value

    @property
    def observer(self) -> Optional[Observer]:
        return self._observer

    # 'private' setter, use change_observer instead.
    @observer.setter
    def observer(self, value: Optional[Observer]) -> None:
        self._observer = value
        self.events.on_observer_changed.fire()
