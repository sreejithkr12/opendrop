import functools
from collections import namedtuple
from typing import Sequence, Optional, Callable, overload, TypeVar, List

from gi.repository import Gtk

from opendrop.app2.ui.observerchooser.observer_chooser_dlg import ObserverChooserDialog, ObserverChooserDialogReceiver
from opendrop.app3.ui.experimentsetup.setup_window import SetupWindowView
from opendrop.mvp3.style_provider_widget_follower import StyleProviderWidgetFollower
from opendrop.observer.bases import Observer, ObserverType
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter, AtomicBindableVar
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.events import EventConnection

T = TypeVar('T')


class SpecificEditorView:
    def __init__(self, *args, **kwargs):
        # region Bindables
        self.bn_frame_interval = AtomicBindableAdapter()  # type: AtomicBindable[Optional[float]]
        self.bn_num_frames = AtomicBindableAdapter()  # type: AtomicBindable[Optional[int]]
        # endregion

    def destroy(self) -> None:
        pass


class SpecificEditorViewFactory:
    SEVConstructor = Callable[['ImageAcquisitionSubview', Gtk.Grid], SpecificEditorView]
    Record = namedtuple('EditorContainer', ('should_edit', 'constructor'))

    _editors = []  # type: List[Record]

    @classmethod
    def new_for_observer(cls, observer: Observer, parent: 'ImageAcquisitionSubview', container: Gtk.Grid)\
            -> SpecificEditorView:
        for (should_edit, constructor) in cls._editors:
            if should_edit(observer):
                return constructor(parent, container)
        else:
            raise ValueError('Could not find an editor for observer `{}`'.format(observer))

    @overload
    @classmethod
    def register(cls, should_edit: Callable[[Observer], bool], constructor: SEVConstructor) -> None: ...

    @overload
    @classmethod
    def register(cls, should_edit: Callable[[Observer], bool]) -> Callable[[T], T]: ...

    @classmethod
    def register(cls, should_edit, constructor=None, _decorator: bool = False):
        if constructor is None:
            return functools.partial(cls.register, should_edit, _decorator=True)

        cls._editors.append(cls.Record(should_edit, constructor))

        if _decorator:
            return constructor


class ImageAcquisitionEditorView:
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

    def __init__(self, parent: 'ImageAcquisitionSubview', container: Gtk.Grid) -> None:
        self._parent = parent
        self._container = container

        self._current_specific_editor_view = None
        self._current_specific_editor_cleanup_fs = []  # type: List[Callable[[], None]]

        self._event_conns = []  # type: List[EventConnection]

        # region Styling boilerplate
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(self.STYLE, encoding='utf-8'))
        css_provider_adder = StyleProviderWidgetFollower(css_provider)
        css_provider_adder.set_target(container)
        # endregion

        # region Bindables
        self.bn_frame_interval = AtomicBindableVar(0)
        self.bn_num_frames = AtomicBindableVar(0)
        self.bn_observer_type_name = AtomicBindableAdapter()  # type: AtomicBindable[str]
        self._event_conns.append(parent.bn_observer.on_changed.connect(self._update_observer_type_name))
        # endregion

        # region Misc. event connections
        self._event_conns.append(parent.bn_observer.on_changed.connect(self._update_specific_editor))
        # endregion

        self._build_ui()
        self._update_observer_type_name()
        self._update_specific_editor()

    def _build_ui(self) -> None:
        body = self._container

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

        # `width_chars=0` for zero minimum width
        observer_type_name = Gtk.Entry(sensitive=False, width_chars=0, hexpand=True)
        observer_type_name.get_style_context().add_class('small')
        observer_type_ctn.attach(observer_type_name, 0, 0, 1, 1)
        self.bn_observer_type_name.setter = observer_type_name.set_text

        change_observer_btn = Gtk.Button('Change')
        change_observer_btn.get_style_context().add_class('small')
        observer_type_ctn.attach(change_observer_btn, 1, 0, 1, 1)
        change_observer_btn.connect('clicked', lambda *_: self._prompt_user_change_observer())

        body.attach(Gtk.Separator(), 0, 1, 2, 1)

        self._specific_ctn = Gtk.Box()
        body.attach(self._specific_ctn, 0, 2, 1, 1)

        # Show children.
        body.foreach(Gtk.Widget.show_all)

    def new_observer_chooser_dlg(self, dlg_rcv: ObserverChooserDialogReceiver, o_types: Sequence[ObserverType])\
            -> 'ImageAcquisitionEditorView.ObserverChooserDlgHandle':
        dlg = ObserverChooserDialog(o_types, modal=True, transient_for=self._container.get_toplevel())
        dlg.connect('delete-event', lambda *_: True)
        dlg_rcv.set_target_dlg(dlg)
        return self.ObserverChooserDlgHandle(dlg)

    def _update_specific_editor(self) -> None:
        # region Clean up/destroy previous specific editor view
        if self._current_specific_editor_view is not None:
            self._specific_ctn.remove(self._specific_ctn.get_children[0])
            self._current_specific_editor_view.destroy()

            for f in self._current_specific_editor_cleanup_fs:
                f()

            self._current_specific_editor_view = None
            self._current_specific_editor_cleanup_fs = []
        # endregion

        observer = self._parent.bn_observer.get()

        if observer is None:
            return

        editor = Gtk.Grid()
        self._current_specific_editor_view = SpecificEditorViewFactory.new_for_observer(
            observer=observer,
            parent=self._parent,
            container=editor
        )

        data_bindings = [
            Binding(self.bn_frame_interval, self._current_specific_editor_view.bn_frame_interval),
            Binding(self.bn_num_frames, self._current_specific_editor_view.bn_num_frames)
        ]

        for binding in data_bindings:
            self._current_specific_editor_cleanup_fs.append(binding.unbind)

        self._specific_ctn.add(editor)
        editor.show()

    def _update_observer_type_name(self) -> None:
        name = 'None'

        observer = self._parent.bn_observer.get()
        if observer is not None:
            name = observer.type.name

        self.bn_observer_type_name.set(name)

    def _prompt_user_change_observer(self) -> None:
        print('change observer')

    def destroy(self) -> None:
        for conn in self._event_conns:
            conn.disconnect()


class ImageAcquisitionSubview:
    ID = 'image_acquisition'

    def __init__(self, parent: SetupWindowView):
        self.bn_observer = AtomicBindableVar(None)  # type: AtomicBindable[Optional[Observer]]
        self.bn_available_observer_types = AtomicBindableAdapter()  # type: AtomicBindable[Sequence[ObserverType]]

        item_hdl = parent._item_explorer.new_item(
            id_=self.ID,
            icon=Gtk.IconTheme.get_default().load_icon(
                icon_name='camera-photo',
                size=16,
                flags=0),
            name='Image acquisition'
        )

        editor = Gtk.Grid()
        self._editor_view = ImageAcquisitionEditorView(self, editor)
        editor.show()
        parent._item_editor_stack.add_named(editor, self.ID)

    @property
    def bn_frame_interval(self) -> AtomicBindable[Optional[float]]:
        return self._editor_view.bn_frame_interval

    @property
    def bn_num_frames(self) -> AtomicBindable[Optional[float]]:
        return self._editor_view.bn_num_frames

    def destroy(self) -> None:
        self._editor_view.destroy()
