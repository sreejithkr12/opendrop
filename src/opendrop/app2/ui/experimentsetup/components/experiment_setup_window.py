from typing import TypeVar, Generic, Any, Optional, Tuple

from gi.repository import Gtk

from opendrop.app2.ui.experimentsetup.canvas import Canvas, ArtboardLayoutType
from opendrop.app2.ui.experimentsetup.components.canvas_viewer import CanvasViewer
from opendrop.app2.ui.experimentsetup.components.obspvctrller.observer_preview_controller import \
    ObserverPreviewController
from opendrop.app2.ui.experimentsetup.configurettes.bases import Configurette
from opendrop.mvp2.gtk.componentstuff.app_win import GtkAppWinComponent, GtkAppWinComponentView
from opendrop.mvp2.gtk.viewstuff.mixins.widget_style_provider_adder import WidgetStyleProviderAdderMixin
from opendrop.mvp2.presenter import Presenter
from opendrop.res import path as res
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.events import Event
from .configuration_sidebar import ConfigurationSidebar


class ObserverPreviewControllerAPI:
    def __init__(self, target: ObserverPreviewController):
        self._target = target
        self.bn_preview = AtomicBindableAdapter()  # type: AtomicBindable[ObserverPreviewController]
        link_atomic_bn_adapter_to_g_prop(self.bn_preview, target, 'preview')

    @AtomicBindable.property_adapter
    def preview(self) -> AtomicBindable[ObserverPreviewController]:
        return self.bn_preview


class ExperimentSetupWindowView(GtkAppWinComponentView, WidgetStyleProviderAdderMixin):
    WINDOW_TITLE = 'Configuration'

    LOGO_PATH = str(res / 'images' / 'logo.png')

    STYLE = '''
    .bg-gainsboro {
        background-color: gainsboro;
    }
    '''

    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(
            self.STYLE, encoding='utf-8'
        ))
        WidgetStyleProviderAdderMixin._m_init(self, css_provider)

        self.bn_canvas_viewer_size = AtomicBindableAdapter()  # type: AtomicBindable[Tuple[int, int]]

        self.preview_controller = None  # type: Optional[ObserverPreviewControllerAPI]

    def _set_up(self) -> None:
        self._set_target_for_style_provider(self.window)
        self.window.set_default_size(800, 600)

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
        self._config_sidebar = ConfigurationSidebar()
        body.attach(self._config_sidebar, 0, 0, 1, 1)
        # </Configuration sidebar>

        body.attach(Gtk.Separator(), 1, 0, 1, 1)

        # <Viewer>
        canvas_viewer_ctn = Gtk.Grid()
        body.attach(canvas_viewer_ctn, 2, 0, 1, 1)

        self._canvas = Canvas((1, 1))
        self._canvas_viewer = CanvasViewer(hexpand=True, vexpand=True)
        canvas_viewer_ctn.attach(self._canvas_viewer, 0, 0, 1, 1)
        self.bn_canvas_viewer_size.getter = self._raw_get_canvas_viewer_size
        self._canvas_viewer.connect('size-allocate', lambda *_: self.bn_canvas_viewer_size.poke())

        preview_controller_wg = ObserverPreviewController()
        preview_controller_wg.get_style_context().add_class('bg-gainsboro')
        canvas_viewer_ctn.attach(preview_controller_wg, 0, 1, 1, 1)

        # Wrapper object for presenter to access `preview_controller_wg`.
        self.preview_controller = ObserverPreviewControllerAPI(preview_controller_wg)
        # </Viewer>

        self.window.add(body)
        # </Body>

        body.show_all()

    def add_configurette(self, cfette: Configurette) -> None:
        self._config_sidebar.add_configurette(cfette)

    @property
    def canvas(self) -> Optional[Canvas]:
        return self._canvas_viewer.props.canvas

    @canvas.setter
    def canvas(self, new_canvas: Optional[Canvas]) -> None:
        self._canvas_viewer.props.canvas = new_canvas

    @AtomicBindable.property_adapter
    def canvas_viewer_size(self) -> AtomicBindable[Tuple[int, int]]:
        return self.bn_canvas_viewer_size

    def _raw_get_canvas_viewer_size(self) -> Tuple[int, int]:
        rect = self._canvas_viewer.get_allocated_size().allocation

        return rect.width, rect.height


CT = TypeVar('CT')


class ExperimentSetupWindowPresenter(Presenter[ExperimentSetupWindowView], Generic[CT]):
    def _m_init(self, model: 'ExperimentSetupWindowModel[CT]', **kwargs):
        super()._m_init(**kwargs)
        self.model = model
        self.canvas = Canvas((1, 1))

    def _set_up(self):
        self.view.canvas = self.canvas

        self.__data_bindings = [
            Binding(self.view.bn_canvas_viewer_size, self.canvas.bn_viewport_size),
        ]

    def _tear_down(self) -> None:
        for binding in self.__data_bindings:
            binding.unbind()


class ExperimentSetupWindowModel(Generic[CT]):
    def __init__(self):
        self.on_config_loaded = Event()  # emits: ()
        self._config_obj = None  # type: Optional[int]

    @property
    def config_obj(self) -> CT:
        return self._config_obj

    @config_obj.setter
    def config_obj(self, config_obj: CT) -> None:
        assert self._config_obj is None
        self._config_obj = config_obj
        self.on_config_loaded.fire()


class _ExperimentSetupWindow(GtkAppWinComponent):
    view = ...  # type: ExperimentSetupWindowView
    presenter = ...  # type: ExperimentSetupWindowPresenter

    def _m_init(self, *args, **kwargs):
        super()._m_init(*args, **kwargs)
        self._model = ExperimentSetupWindowModel()
        self._presenter_opts['model'] = self._model

    def _set_up(self) -> None:
        # Connect to view events.
        self._event_conns = []

        # Set up view and presenter.
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self) -> None:
        # Disconnect event connections.
        for conn in self._event_conns:
            conn.disconnect()

        # Tear down view and presenter.
        self.presenter.tear_down()
        self.view.tear_down()

    def set_config_obj(self, config_obj: Any) -> None:
        self._model.config_obj = config_obj


class ExperimentSetupWindow(_ExperimentSetupWindow):
    def __init__(self, *args, **kwargs):
        default_clses = {'_view_cls': ExperimentSetupWindowView, '_presenter_cls': ExperimentSetupWindowPresenter}
        kwargs = {**default_clses, **kwargs}
        super().__init__(*args, **kwargs)
