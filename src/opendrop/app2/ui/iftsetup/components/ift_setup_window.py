from typing import Optional

import cv2
import numpy as np
from gi.repository import GLib

from opendrop.app2.analysis import IFTAnalysisConfiguration
from opendrop.app2.ui.experimentsetup.canvas import CanvasLayer, CanvasContext, CanvasArtboard, \
    ObserverPreviewCanvasArtboard, ArtboardLayoutType
from opendrop.observer.bases import ObserverPreview
from ...experimentsetup.components.experiment_setup_window import ExperimentSetupWindowPresenter, ExperimentSetupWindow, \
    ExperimentSetupWindowView
from ...experimentsetup.configurettes.canny_edge_detection import CannyEdgeDetectionConfigurette
from ...experimentsetup.configurettes.imageacquisition.image_acquisition import ImageAcquisitionConfigurette


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


class IFTSetupWindowView(ExperimentSetupWindowView):
    def _m_init(self, **kwargs):
        super()._m_init(**kwargs)

        self.imacq_config = None
        self.canny_config = None
        
    def load_config(self, config: IFTAnalysisConfiguration) -> None:
        imacq_config = ImageAcquisitionConfiguration(config)
        imacq_cfette = ImageAcquisitionConfigurette(imacq_config)
        self._config_sidebar.add_configurette(imacq_cfette)

        canny_edge_detection_config = CannyEdgeDetectionConfiguration(config)
        canny_edge_detection_cfette = CannyEdgeDetectionConfigurette(canny_edge_detection_config)
        self._config_sidebar.add_configurette(canny_edge_detection_cfette)


class IFTSetupWindowPresenter(ExperimentSetupWindowPresenter[IFTAnalysisConfiguration]):
    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)
        self._observer_preview = None  # type: Optional[ObserverPreview]

    def _set_up(self) -> None:
        super()._set_up()
        self.__event_conns = [
            self.model.on_config_loaded.connect(self.hdl_model_config_loaded)
        ]

    def _tear_down(self) -> None:
        super()._tear_down()
        for conn in self.__event_conns:
            conn.disconnect()

        if self._observer_preview is not None:
            self._observer_preview.close()

    def hdl_model_config_loaded(self) -> None:
        config_obj = self.model.config_obj
        self.view.load_config(config_obj)

        # observer_config = ImageAcquisitionConfiguration(config_obj)
        # observer_cfette = ImageAcquisitionConfigurette(observer_config)
        # self.view.add_configurette(observer_cfette)
        #
        # canny_edge_detection_config = CannyEdgeDetectionConfiguration(config_obj)
        # canny_edge_detection_cfette = CannyEdgeDetectionConfigurette(canny_edge_detection_config)
        # self.view.add_configurette(canny_edge_detection_cfette)
        #
        config_obj.bn_observer.on_changed.connect(self.update_preview, immediate=True)
        self.update_preview()

    def update_preview(self) -> None:
        if self._observer_preview is not None:
            self._observer_preview.close()
            self._observer_preview = None

        observer = self.model.config_obj.observer

        if observer is None:
            self.canvas.artboard = None
            return

        self._observer_preview = self.model.config_obj.observer.preview()
        self.canvas.artboard = ObserverPreviewCanvasArtboard(self._observer_preview)
        self.canvas.artboard_layout = ArtboardLayoutType.FIT

        self.view.preview_controller.preview = self._observer_preview


class IFTSetupWindow(ExperimentSetupWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=IFTSetupWindowView,
            _presenter_cls=IFTSetupWindowPresenter,
            *args, **kwargs,
        )
