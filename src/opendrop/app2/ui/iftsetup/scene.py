from opendrop.app2.ui.experimentsetup.scene import ExperimentSetupScene
from opendrop.app2.ui.iftsetup.components.ift_setup_window import IFTSetupWindow


class IFTSetupScene(ExperimentSetupScene):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _setup_win_cls=IFTSetupWindow,
            *args, **kwargs
        )
