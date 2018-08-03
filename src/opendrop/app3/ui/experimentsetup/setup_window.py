from typing import Optional

from gi.repository import GObject, Gtk

from opendrop.app2.ui.experimentsetup.canvas import Canvas
from opendrop.app2.ui.experimentsetup.components.canvas_viewer import CanvasViewer
from opendrop.app2.ui.experimentsetup.components.obspvctrller.observer_preview_controller import \
    ObserverPreviewController
from opendrop.mvp3.style_provider_widget_follower import StyleProviderWidgetFollower
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.app3.ui.experimentsetup.item_explorer import ItemExplorer


class ObserverPreviewControllerAPI:
    def __init__(self, target: ObserverPreviewController):
        self._target = target
        self.bn_preview = AtomicBindableAdapter()  # type: AtomicBindable[ObserverPreviewController]
        link_atomic_bn_adapter_to_g_prop(self.bn_preview, target, 'preview')

    @AtomicBindable.property_adapter
    def preview(self) -> AtomicBindable[ObserverPreviewController]:
        return self.bn_preview


class EmptyEditor(Gtk.Label):
    def __init__(self):
        super().__init__(justify=Gtk.Justification.CENTER, wrap=True)
        self.set_markup(
            '<span font_desc=\'11.0\'>{}</span>'
            .format('Select an item to configure.')
        )


class SetupWindowView:
    WINDOW_TITLE = 'Configuration'

    STYLE = '''
    .bg-gainsboro {
        background-color: gainsboro;
    }
    '''

    def __init__(self, window: Gtk.Window) -> None:
        self._window = window

        # region Styling boilerplate
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(self.STYLE, encoding='utf-8'))
        css_provider_adder = StyleProviderWidgetFollower(css_provider)
        css_provider_adder.set_target(window)
        # endregion

        self._canvas = Canvas((1, 1))

        self.preview_controller = None  # type: Optional[ObserverPreviewControllerAPI]

        self._build_ui()
        self._update_canvas_size()

        # region Subviews
        from .subviews.imageacquisition.image_acquisition import ImageAcquisitionSubview
        from .subviews.canny_edge_detection import CannyEdgeDetectionSubview

        image_acquisition = ImageAcquisitionSubview(self)
        self.bn_observer = image_acquisition.bn_observer
        self.bn_frame_interval = image_acquisition.bn_frame_interval
        self.bn_num_frames = image_acquisition.bn_num_frames
        self.bn_available_observer_types = image_acquisition.bn_available_observer_types

        canny_edge_detection = CannyEdgeDetectionSubview(self)
        self.bn_canny_min_thresh = canny_edge_detection.bn_min_thresh
        self.bn_canny_max_thresh = canny_edge_detection.bn_max_thresh
        # endregion

    def _build_ui(self) -> None:
        self._window.set_default_size(800, 600)

        # -- Build UI --

        # <Body>
        body = Gtk.Grid()

        # <Navigation bar>
        navigation_bar = Gtk.Grid(column_spacing=5, margin=5)
        body.attach(Gtk.Separator(), 0, 1, 3, 1)
        body.attach(navigation_bar, 0, 2, 3, 1)

        # <Cancel button>
        cancel_btn = Gtk.Button(label='Cancel')
        navigation_bar.attach(cancel_btn, 0, 0, 1, 1)
        # </Cancel button>

        # <Begin button>
        begin_btn = Gtk.Button(label='Begin', hexpand=True, halign=Gtk.Align.END)
        navigation_bar.attach(begin_btn, 1, 0, 1, 1)
        # </Begin button>

        # </Navigation bar>

        # <Configuration sidebar>
        config_sidebar = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL, hexpand=False, width_request=200)

        self._item_explorer = ItemExplorer(expand=True, height_request=100)

        item_editor_stack_ctn = Gtk.ScrolledWindow(expand=True, height_request=100)
        self._item_editor_stack = Gtk.Stack(expand=True, vhomogeneous=False, height_request=100)
        item_editor_stack_ctn.add(self._item_editor_stack)

        config_sidebar.pack1(self._item_explorer, resize=True, shrink=False)
        config_sidebar.pack2(item_editor_stack_ctn, resize=True, shrink=False)

        empty_editor = EmptyEditor()
        self._item_editor_stack.add_named(empty_editor, '__empty')

        self._item_explorer.bind_property(
            'selection',
            self._item_editor_stack, 'visible-child-name',
            GObject.BindingFlags.DEFAULT,
            lambda _, v: v or '__empty'
        )

        body.attach(config_sidebar, 0, 0, 1, 1)
        # </Configuration sidebar>

        body.attach(Gtk.Separator(), 1, 0, 1, 1)

        # <Viewer>
        canvas_viewer_ctn = Gtk.Grid()
        body.attach(canvas_viewer_ctn, 2, 0, 1, 1)

        self._canvas_viewer = CanvasViewer(hexpand=True, vexpand=True)
        canvas_viewer_ctn.attach(self._canvas_viewer, 0, 0, 1, 1)
        self._canvas_viewer.connect('size-allocate', lambda *_: self._update_canvas_size())

        preview_controller_wg = ObserverPreviewController()
        preview_controller_wg.get_style_context().add_class('bg-gainsboro')
        canvas_viewer_ctn.attach(preview_controller_wg, 0, 1, 1, 1)

        # Wrapper object for presenter to access `preview_controller_wg`.
        self.preview_controller = ObserverPreviewControllerAPI(preview_controller_wg)
        # </Viewer>

        self._window.add(body)
        # </Body>

        body.show_all()

    def _update_canvas_size(self) -> None:
        rect = self._canvas_viewer.get_allocated_size().allocation
        self._canvas.viewport_size = rect.width, rect.height
