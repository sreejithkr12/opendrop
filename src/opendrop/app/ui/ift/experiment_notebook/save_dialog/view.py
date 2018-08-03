from pathlib import Path
from typing import Optional

from gi.repository import Gtk

from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.utility import data_binding
from opendrop.widgets.float_entry import FloatEntry


class SaveDialogView(GtkWindowView):
    def setup(self):
        self.window.props.resizable = False

        body = Gtk.Grid()
        self.window.add(body)

        conf = Gtk.Grid(margin=10, column_spacing=10, row_spacing=10)
        body.attach(conf, 0, 0, 1, 1)

        save_dir_lbl = Gtk.Label('Save directory:', halign=Gtk.Align.START)
        conf.attach(save_dir_lbl, 0, 0, 1, 1)

        self.save_dir_input = Gtk.FileChooserButton(action=Gtk.FileChooserAction.SELECT_FOLDER, hexpand=True)
        conf.attach(self.save_dir_input, 1, 0, 1, 1)
        self.save_dir_input.connect('selection-changed', lambda w: data_binding.poke(self, type(self).save_parent_dir))

        save_name_lbl = Gtk.Label('Name:', halign=Gtk.Align.START)
        conf.attach(save_name_lbl, 0, 1, 1, 1)

        self.save_name_input = Gtk.Entry()
        conf.attach(self.save_name_input, 1, 1, 1, 1)
        self.save_name_input.connect('changed', lambda w: data_binding.poke(self, type(self).save_name))

        graph_dpi_lbl = Gtk.Label('Figure DPI:', halign=Gtk.Align.START)
        conf.attach(graph_dpi_lbl, 0, 2, 1, 1)

        self.graph_dpi_input = FloatEntry(min=0, max=10000)
        conf.attach(self.graph_dpi_input, 1, 2, 1, 1)
        self.graph_dpi_input.connect('changed', lambda w: data_binding.poke(self, type(self).graph_dpi))

        save_btn = Gtk.Button('Save')
        body.attach(save_btn, 0, 1, 1, 1)
        save_btn.connect('clicked', lambda w: self.events.on_save_btn_clicked.fire())

        self.window.show_all()

    @data_binding.property
    def save_parent_dir(self) -> Optional[str]:
        return self.save_dir_input.get_filename()

    @save_parent_dir.setter
    def save_parent_dir(self, value: Optional[str]) -> None:
        if value is None:
            self.save_dir_input.unselect_all()
            return

        self.save_dir_input.set_filename(value)

    @data_binding.property
    def save_name(self) -> Optional[str]:
        return self.save_name_input.props.text

    @save_name.setter
    def save_name(self, value: Optional[str]) -> None:
        self.save_name_input.props.text = value

    @data_binding.property
    def graph_dpi(self) -> Optional[float]:
        return self.graph_dpi_input.props.value

    @graph_dpi.setter
    def graph_dpi(self, value: Optional[float]) -> None:
        self.graph_dpi_input.props.value = value
