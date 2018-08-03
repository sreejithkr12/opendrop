from typing import Optional

from gi.repository import Gtk, Gdk


class StyleProviderWidgetFollower:
    def __init__(self, style_provider: Gtk.StyleProvider) -> None:
        self._target = None  # type: Optional[Gtk.Widget]
        self._style_provider = style_provider

    def set_target(self, target: Gtk.Widget) -> None:
        assert self._target is None
        self._target = target

        target.connect('screen-changed', self._update_screen_style_provider)
        # Invoke handler to add provider to current screen.
        self._update_screen_style_provider(target, None)

    def _update_screen_style_provider(self, target: Gtk.Container, previous_screen: Optional[Gdk.Screen]) -> None:
        if previous_screen is not None:
            Gtk.StyleContext.remove_provider_for_screen(previous_screen, self._style_provider)

        if target.has_screen():
            Gtk.StyleContext.add_provider_for_screen(target.get_screen(), self._style_provider,
                                                     Gtk.STYLE_PROVIDER_PRIORITY_USER)
