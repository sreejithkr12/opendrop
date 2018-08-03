import math
from typing import Optional, Tuple, NewType, MutableMapping, Any, List

from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup
from opendrop.app.settings import settings
from opendrop.utility import data_binding
from .drop_snapshot import DropSnapshot
from .experiment_notebook import ExperimentNotebook

PointFloat2D = NewType('PointFloat2D', Tuple[float, float])
RectFloat = NewType('RectFloat', Tuple[PointFloat2D, PointFloat2D])


class IFTExperimentSetup(ExperimentSetup):
    def __init__(self):
        super().__init__()

        self.gravity = settings.gravity

        self._inner_density = None  # 1000 #None  # type: Optional[float]
        self._outer_density = None  # 0 #None   # type: Optional[float]
        self._drop_region = ((0, 0), (0, 0))  #[[ 0.15263158, 0.18025288], [ 0.63684211, 0.7394634 ]]  #((0, 0), (0, 0))  # type: RectFloat # [[0.36315789, 0.1901727 ], [ 0.8, 0.76912007]]  #
        #TODO: scale is in nm
        self._scale = math.nan  #6.63792307493311/1000  # math.nan  # type: Optional[float]
        self._needle_width = 0.7176  # type: Optional[float]

    def start_experiment(self) -> ExperimentNotebook:
        #assert not self.validate()

        drop_snapshots = [
            DropSnapshot(observation, self.postproc, self.drop_region, self.scale, self.needle_width,
                         self.inner_density, self.outer_density, self.gravity)
            for observation in self.observer.timelapse(self.frame_timestamps)
        ]  # type: List[DropSnapshot]

        return ExperimentNotebook(drop_snapshots)

    @data_binding.property
    def drop_region(self) -> RectFloat:
        return self._drop_region

    @drop_region.setter
    def drop_region(self, value: RectFloat) -> None:
        self._drop_region = value

        self.events.on_drop_region_changed.fire()

    @data_binding.property
    def inner_density(self) -> float:
        return self._inner_density

    @inner_density.setter
    def inner_density(self, value: float) -> None:
        self._inner_density = value

        self.validate()

    @data_binding.property
    def outer_density(self) -> float:
        return self._outer_density

    @outer_density.setter
    def outer_density(self, value: float) -> None:
        self._outer_density = value

        self.validate()

    @data_binding.property
    def needle_width(self) -> float:
        return self._needle_width

    @needle_width.setter
    def needle_width(self, value: float) -> None:
        self._needle_width = value

        self.events.on_needle_width_changed.fire()

        self.validate()

    @data_binding.property
    def scale(self) -> Optional[float]:
        return self._scale

    @scale.setter
    def scale(self, value: Optional[float]) -> None:
        if math.isnan(value):
            value = None

        self._scale = value

        self.validate()

    def validate(self) -> MutableMapping[str, Any]:
        errors = {}  # type: MutableMapping[str, Any]

        if self.inner_density is None:
            errors['inner_density'] = "Inner density can't be blank"
        elif self.inner_density < 0:
            errors['inner_density'] = "Inner density must be positive"

        if self.outer_density is None:
            errors['outer_density'] = "Outer density can't be blank"
        elif self.outer_density < 0:
            errors['outer_density'] = "Outer density must be positive"

        if self.needle_width is None:
            errors['needle_width'] = "Needle diameter can't be blank"
        elif self.needle_width < 0:
            errors['needle_width'] = "Needle diameter must be positive"

        if not self.frame_timestamps:
            errors['frame_timestamps'] = "Frame timestamps can't be empty"
        elif sum([math.isnan(x) or math.isinf(x) for x in self.frame_timestamps]):
            errors['frame_timestamps'] = "Frame timestamps can't contain `inf` or `nan`"

        if self.drop_region[1][0] - self.drop_region[0][0] == 0 or self.drop_region[1][1] - self.drop_region[0][1] == 0:
            errors['drop_region'] = "Drop region can't have zero height/width"

        if self.scale is None:
            errors['scale'] = "Scale can't be blank"
        elif self.scale < 0:
            errors['scale'] = "Scale must be positive"

        return errors
