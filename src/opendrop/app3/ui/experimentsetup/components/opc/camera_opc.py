from gi.repository import Gtk

from opendrop.observer.types.camera import CameraObserverPreview
from .opc import ObserverPreviewControllerFactory


@ObserverPreviewControllerFactory.register_controller(lambda preview: isinstance(preview, CameraObserverPreview))
class CameraObserverPreviewController(Gtk.Box):
    def __init__(self, preview: CameraObserverPreview):
        # Basically an empty widget since there's nothing to control for a live camera preview.
        super().__init__()
