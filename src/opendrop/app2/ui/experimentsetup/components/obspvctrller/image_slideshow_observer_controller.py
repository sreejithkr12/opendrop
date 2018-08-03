import functools
import math
from typing import Optional

from gi.repository import Gtk

from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponentView, GtkGridComponent
from opendrop.mvp2.gtk.viewstuff.mixins.widget_style_provider_adder import WidgetStyleProviderAdderMixin
from opendrop.mvp2.presenter import Presenter
from opendrop.observer.types.image_slideshow import ImageSlideshowObserverPreview
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding, AtomicBindingMITM
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.events import Event
from opendrop.widgets.integer_entry import IntegerEntry
from .observer_preview_controller import ObserverPreviewControllerProvider


class ImageSlideshowObserverPreviewControllerView(GtkGridComponentView, WidgetStyleProviderAdderMixin):
    STYLE = '''
    .small {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
    }
    
    .minimum {
        min-height: 0px;
        min-width: 0px;
    }
    '''

    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(
            self.STYLE, encoding='utf-8'
        ))
        WidgetStyleProviderAdderMixin._m_init(self, css_provider)

        self.on_backward_btn_clicked = Event()  # emits: ()
        self.on_forward_btn_clicked = Event()  # emits: ()

        self.bn_num_images = AtomicBindableAdapter()  # type: AtomicBindable[int]
        self.bn_show_index = AtomicBindableAdapter()  # type: AtomicBindable[Optional[int]]

    def _set_up(self):
        body = self.container
        self._set_target_for_style_provider(body)

        body.props.margin         = 5
        body.props.column_spacing = 5
        body.props.row_spacing    = 5
        body.props.hexpand        = True
        body.props.halign         = Gtk.Align.CENTER

        backward_btn = Gtk.Button.new_from_icon_name('media-skip-backward', Gtk.IconSize.SMALL_TOOLBAR)  # type: Gtk.Button
        backward_btn.get_style_context().add_class('minimum')
        backward_btn.connect('clicked', lambda *_: self.on_backward_btn_clicked.fire())

        body.attach(backward_btn, 0, 0, 1, 1)

        self.preview_index_inp = IntegerEntry(lower=1, default=1, width_chars=1, xalign=1, valign=Gtk.Align.CENTER)
        self.preview_index_inp.get_style_context().add_class('small')

        link_atomic_bn_adapter_to_g_prop(self.bn_show_index, self.preview_index_inp, 'value')
        self.bn_num_images.setter = self._set_num_images

        body.attach(self.preview_index_inp, 1, 0, 1, 1)

        self.num_images_lbl = Gtk.Label()

        body.attach(self.num_images_lbl, 2, 0, 1, 1)

        forward_btn = Gtk.Button.new_from_icon_name('media-skip-forward', Gtk.IconSize.SMALL_TOOLBAR)  # type: Gtk.Button
        forward_btn.get_style_context().add_class('minimum')
        forward_btn.connect('clicked', lambda *_: self.on_forward_btn_clicked.fire())

        body.attach(forward_btn, 3, 0, 1, 1)

        body.foreach(Gtk.Widget.show)

    def _set_num_images(self, num_images: int) -> None:
        assert num_images > 0
        self.preview_index_inp.props.upper = num_images
        self.preview_index_inp.props.width_chars = int(math.log10(num_images)) + 2
        self.num_images_lbl.props.label = 'of {}'.format(num_images)


class ImageSlideshowObserverPreviewControllerPresenter(Presenter[ImageSlideshowObserverPreviewControllerView]):
    def _m_init(self, preview: ImageSlideshowObserverPreview) -> None:
        self.preview = preview

    def _set_up(self):
        self._data_bindings = [
            Binding(self.preview.bn_num_images, self.view.bn_num_images),
            Binding(self.preview.bn_show_index, self.view.bn_show_index, mitm=AtomicBindingMITM(
                # Internally, each image is zero-based indexed, but show the user one-based indices.
                to_dst=lambda i: i+1,
                to_src=lambda i: i-1,
            ))
        ]

        self._event_conns = [
            self.view.on_forward_btn_clicked.connect(self.show_index_increment),
            self.view.on_backward_btn_clicked.connect(self.show_index_decrement)
        ]

    def _tear_down(self):
        for binding in self._data_bindings:
            binding.unbind()

        for conn in self._event_conns:
            conn.disconnect()

    def show_index_increment(self) -> None:
        curr = self.preview.show_index
        incd = (curr + 1) % self.preview.num_images
        self.preview.show_index = incd

    def show_index_decrement(self) -> None:
        curr = self.preview.show_index
        decd = (curr - 1) % self.preview.num_images
        self.preview.show_index = decd


class _ImageSlideshowObserverPreviewController(GtkGridComponent):
    def _m_init(self, preview: ImageSlideshowObserverPreview, *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)
        self._presenter_opts['preview'] = preview

    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()


@ObserverPreviewControllerProvider.register_controller(
    lambda preview: isinstance(preview, ImageSlideshowObserverPreview)
)
class ImageSlideshowObserverPreviewController(_ImageSlideshowObserverPreviewController):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ImageSlideshowObserverPreviewControllerView,
            _presenter_cls=ImageSlideshowObserverPreviewControllerPresenter,
            *args, **kwargs
        )
