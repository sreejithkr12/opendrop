import math
from typing import Mapping, Any, Optional

from opendrop import observer
from opendrop.observer.bases import ObserverType, Observer
from opendrop.observer.service import ObserverService
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable, AtomicBindableAdapter

GRAVITY = 9.80035


class IFTAnalysisConfiguration:
    def __init__(self, parent: 'IFTAnalysis'):
        self._parent = parent

        self.available_observer_types = parent.observer_service.get_types()

        self.bn_observer = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Observer]]
        self.bn_num_frames = AtomicBindableVar(None)  # type: AtomicBindable[Optional[int]]
        self.bn_frame_interval = AtomicBindableVar(None)  # type: AtomicBindable[Optional[float]]

        self.bn_canny_min_thresh = AtomicBindableVar(30)
        self.bn_canny_max_thresh = AtomicBindableVar(60)

        self.bn_inner_density = AtomicBindableVar(None)
        self.bn_outer_density = AtomicBindableVar(None)

        self.bn_gravity = AtomicBindableVar(GRAVITY)

        self.bn_scale = AtomicBindableVar(math.nan)  #6.63792307493311/1000  # math.nan  # type: Optional[float]
        self.bn_needle_width = AtomicBindableVar(0.7176)

    def change_observer(self, new_observer_type: ObserverType, new_observer_options: Mapping[str, Any]) -> None:
        self.bn_observer.set(self._parent.observer_service.new_observer_by_type(
            o_type=new_observer_type,
            **new_observer_options
        ))

    @AtomicBindable.property_adapter
    def observer(self) -> AtomicBindable[Optional[Observer]]: return self.bn_observer


class IFTAnalysis:
    observer_service = ObserverService(observer.types.get_all_types())

    def __init__(self):
        self.config = IFTAnalysisConfiguration(self)
