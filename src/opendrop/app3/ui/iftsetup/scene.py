from opendrop.app3.ui.experimentsetup.scene import ExperimentSetupScene
from opendrop.app3.ui.iftsetup.components.ift_setup_window import IFTSetupWindowView, IFTSetupWindowPresenter


class IFTSetupScene(ExperimentSetupScene):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _setup_win_view_cls=IFTSetupWindowView,
            _setup_win_presenter_cls=IFTSetupWindowPresenter,
            *args, **kwargs
        )
