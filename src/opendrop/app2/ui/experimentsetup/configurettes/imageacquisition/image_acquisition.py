import functools
import gc
import warnings
from abc import abstractmethod
from collections import namedtuple
from typing import Sequence, Mapping, Any, Optional, Callable, overload, TypeVar, List

from gi.repository import Gtk, GLib
from typing_extensions import Protocol

from opendrop.app2.ui.observerchooser.observer_chooser_dlg import ObserverChooserDialog, ObserverChooserDialogReceiver
from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponent, GtkGridComponentView
from opendrop.mvp2.gtk.viewstuff.mixins.widget_style_provider_adder import WidgetStyleProviderAdderMixin
from opendrop.mvp2.presenter import Presenter
from opendrop.observer.bases import Observer, ObserverType
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter
from opendrop.utility.bindable.binding import Binding, AtomicBindingMITM
from opendrop.utility.events import Event
from ..bases import Configurette

T = TypeVar('T')


class ObserverSpecificImAcqEditorProvider:
    RealEditorProvider = Callable[['ObserverModelProtocol'], Gtk.Widget]
    EditorContainer = namedtuple('EditorContainer', ('should_edit', 'provider'))

    _editors = []  # type: List[EditorContainer]

    @classmethod
    def new_for_observer(cls, observer: Observer, model: 'ImageAcquisitionConfigurationModel') -> Gtk.Widget:
        for (should_edit, editor_provider) in cls._editors:
            if not should_edit(observer): continue
            return editor_provider(model)
        else:
            raise ValueError('Could not find an editor for imageacquisition `{}`'.format(observer))

    @overload
    @classmethod
    def register(cls, should_edit: Callable[[Observer], bool], provider: RealEditorProvider) -> None: ...

    @overload
    @classmethod
    def register(cls, should_edit: Callable[[Observer], bool]) -> Callable[[T], T]: ...

    @classmethod
    def register(cls, should_edit, provider=None, _decorator: bool = False):
        if provider is None:
            return functools.partial(cls.register, should_edit, _decorator=True)

        cls._editors.append(cls.EditorContainer(should_edit, provider))

        if _decorator:
            return provider


class ImageAcquisitionEditorView(GtkGridComponentView, WidgetStyleProviderAdderMixin):
    STYLE = '''
    .small {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }
    '''

    class ObserverChooserDlgHandle:
        def __init__(self, target_dlg: ObserverChooserDialog):
            self._target_dlg = target_dlg

        def show(self) -> None:
            self._target_dlg.show()

        def destroy(self) -> None:
            self._target_dlg.destroy()

    def _m_init(self, *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(
            self.STYLE, encoding='utf-8'
        ))
        WidgetStyleProviderAdderMixin._m_init(self, css_provider)

        self.bn_observer_type_name = AtomicBindableAdapter()  # type: AtomicBindable[str]

        self.on_edit_btn_clicked = Event()  # emits: ()

        self._current_specific_editor = None  # Optional[Gtk.Widget]

    def _set_up(self) -> None:
        body = self.container

        self._set_target_for_style_provider(body)

        body.props.margin         = 10
        body.props.margin_top     = 15
        body.props.margin_bottom  = 15
        body.props.row_spacing    = 10

        common_ctn = Gtk.Grid(column_spacing=10)
        body.attach(common_ctn, 0, 0, 1, 1)

        frame_interval_lbl = Gtk.Label('Observer:', halign=Gtk.Align.START)
        common_ctn.attach(frame_interval_lbl, 0, 0, 1, 1)

        observer_type_ctn = Gtk.Grid()
        observer_type_ctn.get_style_context().add_class('linked')
        common_ctn.attach(observer_type_ctn, 1, 0, 1, 1)

        # width_chars=0 for zero minimum width
        observer_type_name = Gtk.Entry(sensitive=False, width_chars=0, hexpand=True)
        observer_type_name.get_style_context().add_class('small')
        observer_type_ctn.attach(observer_type_name, 0, 0, 1, 1)

        self.bn_observer_type_name.setter = observer_type_name.set_text

        change_observer_btn = Gtk.Button('Change')
        change_observer_btn.get_style_context().add_class('small')
        observer_type_ctn.attach(change_observer_btn, 1, 0, 1, 1)
        change_observer_btn.connect('clicked', lambda *_: self.on_edit_btn_clicked.fire())

        body.attach(Gtk.Separator(), 0, 1, 2, 1)

        self._specific_ctn = Gtk.Box()#column_spacing=10, row_spacing=5)
        body.attach(self._specific_ctn, 0, 2, 1, 1)

        # Show children.
        body.foreach(Gtk.Widget.show_all)

    def new_observer_chooser_dlg(self, dlg_rcv: ObserverChooserDialogReceiver, o_types: Sequence[ObserverType])\
            -> 'ImageAcquisitionEditorView.ObserverChooserDlgHandle':
        dlg = ObserverChooserDialog(o_types, modal=True, transient_for=self.container.get_toplevel())
        dlg.connect('delete-event', lambda *_: True)
        dlg_rcv.set_target_dlg(dlg)
        return self.ObserverChooserDlgHandle(dlg)

    def _update_specific_editor(self, new_editor: Gtk.Widget) -> None:
        if self._current_specific_editor is not None:
            self._specific_ctn.remove(self._current_specific_editor)
            self._current_specific_editor.destroy()
            self._current_specific_editor = None

        if new_editor is None:
            return

        self._specific_ctn.add(new_editor)
        self._current_specific_editor = new_editor
        new_editor.show()


class ImageAcquisitionEditorPresenter(Presenter[ImageAcquisitionEditorView]):
    def _m_init(self, model: 'ImageAcquisitionConfigurationModel', **kwargs) -> None:
        super()._m_init(**kwargs)
        self.model = model

        self.active_dlg_h = None  # type: Optional[ImageAcquisitionEditorView.ObserverChooserDlgHandle]

    def _set_up(self) -> None:
        self._data_bindings = [
            Binding(self.model.bn_observer, self.view.bn_observer_type_name,
                    mitm=AtomicBindingMITM(
                        to_dst=lambda o: o.type.name,
                        to_src=lambda _: warnings.warn(
                            "this shouldn't have changed"
                        )  # stub, view.bn_observer_type_name shouldn't change anyway.
                    ))
        ]

        self._event_conns = [
            self.view.on_edit_btn_clicked.connect(self.prompt_user_change_observer, immediate=True),
            self.model.bn_observer.on_changed.connect(self.update_view_specific_editor, immediate=True)
        ]

        self.update_view_specific_editor()

    def _tear_down(self) -> None:
        for binding in self._data_bindings:
            binding.unbind()

        for conn in self._event_conns:
            conn.disconnect()

    def update_view_specific_editor(self) -> None:
        new_observer = self.model.bn_observer.get()

        if new_observer is None:
            self.view._update_specific_editor(None)
            return

        observer_specific_editor = ObserverSpecificImAcqEditorProvider.new_for_observer(new_observer, self.model)
        self.view._update_specific_editor(observer_specific_editor)

    def prompt_user_change_observer(self) -> None:
        if self.active_dlg_h:
            return

        outer = self

        class Receiver(ObserverChooserDialogReceiver):
            def response_ok(self):
                outer.model.change_observer(self.observer_type, self.options)
                self.done()

            def response_cancel(self):
                self.done()

            def done(self):
                outer.active_dlg_h.destroy()
                outer.active_dlg_h = None

        self.active_dlg_h = self.view.new_observer_chooser_dlg(Receiver(), self.model.available_observer_types)
        self.active_dlg_h.show()


class ImageAcquisitionConfigurationModel(Protocol):
    @property
    @abstractmethod
    def bn_observer(self) -> AtomicBindable[Observer]:
        """AtomicBindable representing the max threshold value."""

    @property
    @abstractmethod
    def bn_num_frames(self) -> AtomicBindable[Optional[int]]:
        """AtomicBindable representing the number of frames."""

    @property
    @abstractmethod
    def bn_frame_interval(self) -> AtomicBindable[Optional[float]]:
        """AtomicBindable representing frame interval."""

    @property
    @abstractmethod
    def available_observer_types(self) -> Sequence[ObserverType]:
        """The available imageacquisition types the user can choose from."""

    @abstractmethod
    def change_observer(self, new_observer_type: ObserverType, new_observer_opts: Mapping[str, Any]) -> None:
        """Change this model's imageacquisition to a new imageacquisition of type `new_observer_type` and initialised with options
        `new_observer_opts`."""


class _ImageAcquisitionEditor(GtkGridComponent):
    view      = ...  # type: ImageAcquisitionEditorView
    presenter = ...  # type: ImageAcquisitionEditorPresenter

    def _m_init(self, model: ImageAcquisitionConfigurationModel, *, hexpand=False, vexpand=False, **properties) -> None:
        super()._m_init(hexpand=hexpand, vexpand=vexpand, **properties)
        self._model = model
        self._presenter_opts['model'] = model

    def _set_up(self):
        # Set up view and presenter.
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self) -> None:
        # Tear down view and presenter.
        self.presenter.tear_down()
        self.view.tear_down()


class ImageAcquisitionEditor(_ImageAcquisitionEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ImageAcquisitionEditorView,
            _presenter_cls=ImageAcquisitionEditorPresenter,
            *args, **kwargs
        )


class ImageAcquisitionConfigurette(Configurette):
    def __init__(self, config_obj: ImageAcquisitionConfigurationModel):
        super().__init__(
            id_='image_acquisition',
            icon=Gtk.IconTheme.get_default().load_icon(
                icon_name='camera-photo',
                size=16,
                flags=0),
            name='Image acquisition'
        )

        self._config_obj = config_obj

    def create_editor(self) -> Gtk.Widget:
        return ImageAcquisitionEditor(self._config_obj)
