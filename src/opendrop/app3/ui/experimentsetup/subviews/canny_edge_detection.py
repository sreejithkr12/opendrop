import itertools

from gi.repository import Gtk, Gdk, GObject

from opendrop.app3.ui.experimentsetup.setup_window import SetupWindowView
from opendrop.mvp3.style_provider_widget_follower import StyleProviderWidgetFollower
from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.widgets.float_entry import FloatEntry


class NoScrollScale(Gtk.Scale):
    """Identical to Gtk.Scale except 'scroll-event' is ignored so it won't block scrolling in a scroll window.
    """

    def do_scroll_event(self, event: Gdk.EventScroll):
        # Ignore the event
        pass


class CannyEdgeDetectionEditorView:
    STYLE = '''
    .small-entry {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
     }
    '''

    def __init__(self, parent: 'CannyEdgeDetectionSubview', container: Gtk.Grid) -> None:
        self._container = container

        # region Styling boilerplate
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(self.STYLE, encoding='utf-8'))
        css_provider_adder = StyleProviderWidgetFollower(css_provider)
        css_provider_adder.set_target(container)
        # endregion

        # region Bindables
        self.bn_min_thresh = parent.bn_min_thresh
        self.bn_max_thresh = parent.bn_max_thresh
        # endregion

        self.max_thresh_inp = Gtk.Adjustment(value=255, lower=1, upper=255)
        self.min_thresh_inp = Gtk.Adjustment(value=0, lower=0, upper=255)
        self.min_thresh_rel_inp = Gtk.Adjustment(value=0, lower=0, upper=1)

        self.max_thresh_inp.bind_property(
            'value',
            self.min_thresh_inp, 'upper'
        )

        self.min_thresh_inp.bind_property(
            'value',
            self.min_thresh_rel_inp, 'value',
            GObject.BindingFlags.BIDIRECTIONAL,
            lambda _, v: v / self.min_thresh_inp.props.upper,
            lambda _, v: v * self.min_thresh_inp.props.upper
        )

        notify_min_thresh_rel_inp_value_hdl_id = \
            self.max_thresh_inp.connect(
                'notify::value',
                lambda *_: self.min_thresh_rel_inp.notify('value')
            )

        bn_max_thresh_poker_hdl_id = \
            self.max_thresh_inp.connect(
                'value-changed',
                lambda *_: self.bn_max_thresh.poke()
            )

        def bn_max_thresh_setter(value: float) -> None:
            self.max_thresh_inp.handler_block(notify_min_thresh_rel_inp_value_hdl_id)
            self.max_thresh_inp.handler_block(bn_max_thresh_poker_hdl_id)

            self.max_thresh_inp.props.value = value
            self.min_thresh_rel_inp.props.value = self.min_thresh_inp.props.value / value

            self.max_thresh_inp.handler_unblock(notify_min_thresh_rel_inp_value_hdl_id)
            self.max_thresh_inp.handler_unblock(bn_max_thresh_poker_hdl_id)

        self.bn_max_thresh.getter = self.max_thresh_inp.get_value
        self.bn_max_thresh.setter = bn_max_thresh_setter

        link_atomic_bn_adapter_to_g_prop(parent.bn_min_thresh, self.min_thresh_inp, 'value')

        self._build_ui()

    def _build_ui(self) -> None:
        body = self._container

        body.props.margin        = 10
        body.props.margin_top    = 15
        body.props.margin_bottom = 15

        max_thresh_lbl = Gtk.Label('Max threshold:', halign=Gtk.Align.START)
        body.attach(max_thresh_lbl, 0, 0, 1, 1)

        max_thresh_ety = FloatEntry(width_chars=5, halign=Gtk.Align.END, xalign=0)
        max_thresh_ety.get_style_context().add_class('small-entry')
        body.attach(max_thresh_ety, 1, 0, 1, 1)

        max_thresh_scl = NoScrollScale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.max_thresh_inp)
        max_thresh_scl.props.hexpand    = True
        max_thresh_scl.props.draw_value = False
        body.attach(max_thresh_scl, 0, 1, 2, 1)

        min_thresh_lbl = Gtk.Label('Min threshold:', halign=Gtk.Align.START, margin_top=10)
        body.attach(min_thresh_lbl, 0, 2, 1, 1)

        min_thresh_ety = FloatEntry(width_chars=5, halign=Gtk.Align.END, xalign=0)
        min_thresh_ety.get_style_context().add_class('small-entry')
        body.attach(min_thresh_ety, 1, 2, 1, 1)

        min_thresh_scl = NoScrollScale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.min_thresh_rel_inp)
        min_thresh_scl.props.hexpand    = True
        min_thresh_scl.props.draw_value = False
        body.attach(min_thresh_scl, 0, 3, 2, 1)

        for (src, targ), prop in itertools.product(
                ((self.max_thresh_inp, max_thresh_ety), (self.min_thresh_inp, min_thresh_ety)),
                ('value', 'lower', 'upper')
        ):
            src.bind_property(
                prop,                                # source_property
                targ, prop,                          # target, target_property
                GObject.BindingFlags.BIDIRECTIONAL
                | GObject.BindingFlags.SYNC_CREATE,  # flags
                lambda _, v: round(v, 1),            # transform_to
                lambda _, v: v                       # transform_from
            )

        # Show children.
        body.foreach(Gtk.Widget.show_all)

    def destroy(self) -> None:
        self.bn_min_thresh.getter = None
        self.bn_min_thresh.setter = None
        self.bn_max_thresh.getter = None
        self.bn_max_thresh.setter = None


class CannyEdgeDetectionSubview:
    ID = 'canny_edge_detection'

    def __init__(self, parent: SetupWindowView):
        self.bn_max_thresh = AtomicBindableAdapter()
        self.bn_min_thresh = AtomicBindableAdapter()

        item_hdl = parent._item_explorer.new_item(
            id_=self.ID,
            icon=Gtk.IconTheme.get_default().load_icon(
                icon_name='image-missing',
                size=16,
                flags=0),
            name='Canny edge detection'
        )

        editor = Gtk.Grid()
        self._editor_view = CannyEdgeDetectionEditorView(self, editor)
        editor.show()
        parent._item_editor_stack.add_named(editor, self.ID)

    def destroy(self) -> None:
        self._editor_view.destroy()
