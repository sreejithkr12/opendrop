from typing import Optional

from gi.repository import Gtk, Gdk


class WidgetStyleProviderAdderMixin:
    def _m_init(self, style_provider: Gtk.StyleProvider) -> None:
        self.__style_provider = style_provider

    def _set_target_for_style_provider(self, target: Gtk.Widget) -> None:
        target.connect('screen-changed', self.__hdl_screen_changed)
        # Invoke handler to add provider to current screen.
        self.__hdl_screen_changed(target, None)

    def __hdl_screen_changed(self, target: Gtk.Container, previous_screen: Optional[Gdk.Screen]) -> None:
        if previous_screen is not None:
            Gtk.StyleContext.remove_provider_for_screen(previous_screen, self.__style_provider)

        if target.has_screen():
            Gtk.StyleContext.add_provider_for_screen(target.get_screen(), self.__style_provider,
                                                     Gtk.STYLE_PROVIDER_PRIORITY_USER)
