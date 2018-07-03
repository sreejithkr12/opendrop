"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Hello World")
        vbox = Gtk.Box(spacing = 20)
        self.add(vbox)

        self.entry = Gtk.Entry()
        self.button = Gtk.Button(label='Click Here')
        self.button.connect('clicked', self.on_button_clicked)
        vbox.pack_start(self.button, True, True, 0)
        vbox.pack_start(self.entry, True, True, 0)


    def on_button_clicked(self, widget):
        print(self.entry.get_text())

win = MyWindow()
win.connect('destroy', Gtk.main_quit)
win.show_all()
Gtk.main()
"""

