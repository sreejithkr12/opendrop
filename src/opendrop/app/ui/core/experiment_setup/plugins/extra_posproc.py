from opendrop.image_filter.dilate import Dilate
from opendrop.image_filter.erode import Erode
from opendrop.image_filter.gaussian_blur import GaussianBlur
from opendrop.image_filter.image_filter_group import ImageFilterGroup
from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup

from .. import plugins
from ..plugin import ExperimentSetupPlugin


class Plugin(ExperimentSetupPlugin):
    @classmethod
    def should_load(cls, model: ExperimentSetup) -> bool:
        return True

    def setup(self) -> None:
        gb = GaussianBlur(3)
        gb.z_index = -1

        closer = ImageFilterGroup()
        closer.z_index = 1

        closer.add(Dilate(2))
        closer.add(Erode(1))

        self.experiment_setup_model.postproc.add(gb)
        self.experiment_setup_model.postproc.add(closer)


plugins.register_plugin(Plugin)