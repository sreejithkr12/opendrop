from opendrop.app3.analysis import IFTAnalysisConfiguration
from opendrop.utility.bindable.binding import Binding
from opendrop.app3.ui.experimentsetup.setup_window import SetupWindowView


class CannyEdgeDetectionConfiguration:
    def __init__(self, parent_config: IFTAnalysisConfiguration):
        self._destroyed = False
        self._event_conns = []

        self.bn_min_thresh = parent_config.bn_canny_min_thresh
        self.bn_max_thresh = parent_config.bn_canny_max_thresh

    def destroy(self) -> None:
        assert not self._destroyed

        for conn in self._event_conns:
            conn.disconnect()

        self._destroyed = True

    def __del__(self):
        assert self._destroyed


class ImageAcquisitionConfiguration:
    def __init__(self, parent_config: IFTAnalysisConfiguration):
        self._destroyed = False
        self._event_conns = []

        self.bn_observer              = parent_config.bn_observer
        self.bn_num_frames            = parent_config.bn_num_frames
        self.bn_frame_interval        = parent_config.bn_frame_interval
        self.available_observer_types = parent_config.available_observer_types
        self.change_observer          = parent_config.change_observer

    def destroy(self) -> None:
        assert not self._destroyed

        for conn in self._event_conns:
            conn.disconnect()

        self._destroyed = True

    def __del__(self):
        assert self._destroyed


class IFTSetupWindowView(SetupWindowView):
    pass


class IFTSetupWindowPresenter:
    def __init__(self, view: IFTSetupWindowView, config_obj: IFTAnalysisConfiguration) -> None:
        self.view = view
        self.config_obj = config_obj
        self._set_up()
        # self._observer_preview = None  # type: Optional[ObserverPreview]

    def _set_up(self) -> None:
        self._event_conns = [
        ]

        self._data_bindings = [
            Binding(self.config_obj.bn_observer, self.view.bn_observer),
            Binding(self.config_obj.bn_frame_interval, self.view.bn_frame_interval),
            Binding(self.config_obj.bn_num_frames, self.view.bn_num_frames),
            Binding(self.config_obj.bn_canny_min_thresh, self.view.bn_canny_min_thresh),
            Binding(self.config_obj.bn_canny_max_thresh, self.view.bn_canny_max_thresh)
        ]

    def destroy(self) -> None:
        for conn in self._event_conns:
            conn.disconnect()

        for binding in self._data_bindings:
            binding.unbind()

        #
        # if self._observer_preview is not None:
        #     self._observer_preview.close()

    # def hdl_model_config_loaded(self) -> None:
    #     config_obj = self.model.config_obj
    #     self.view.load_config(config_obj)
    #
    #     # observer_config = ImageAcquisitionConfiguration(config_obj)
    #     # observer_cfette = ImageAcquisitionConfigurette(observer_config)
    #     # self.view.add_configurette(observer_cfette)
    #     #
    #     # canny_edge_detection_config = CannyEdgeDetectionConfiguration(config_obj)
    #     # canny_edge_detection_cfette = CannyEdgeDetectionConfigurette(canny_edge_detection_config)
    #     # self.view.add_configurette(canny_edge_detection_cfette)
    #     #
    #     config_obj.bn_observer.on_changed.connect(self.update_preview, immediate=True)
    #     self.update_preview()
    #
    # def update_preview(self) -> None:
    #     if self._observer_preview is not None:
    #         self._observer_preview.close()
    #         self._observer_preview = None
    #
    #     observer = self.model.config_obj.observer
    #
    #     if observer is None:
    #         self.canvas.artboard = None
    #         return
    #
    #     self._observer_preview = self.model.config_obj.observer.preview()
    #     self.canvas.artboard = ObserverPreviewCanvasArtboard(self._observer_preview)
    #     self.canvas.artboard_layout = ArtboardLayoutType.FIT
    #
    #     self.view.preview_controller.preview = self._observer_preview
