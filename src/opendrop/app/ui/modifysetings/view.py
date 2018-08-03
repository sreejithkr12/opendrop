from gi.repository import GObject, Gtk


from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.utility import data_binding
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry


class Header(Gtk.Grid):
    _label = ''

    def __init__(self, vexpand: bool = False, **opts):
        super().__init__(vexpand=vexpand, **opts)

        lbl = Gtk.Label(margin_right=5)
        lbl.set_markup('<span font-desc="11"><b>{}</b></span>'.format(self.props.label))
        self.attach(lbl, 0, 0, 1, 1)

        line = Gtk.Grid(vexpand=False)
        line.attach(Gtk.Grid(hexpand=True, vexpand=True), 0, 0, 1, 1)
        sep = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        sep.props.margin_bottom = 3
        line.attach(sep, 0, 1, 1, 1)
        self.attach(line, 1, 0, 1, 1)

    @GObject.Property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label = value


class ModifySettingsView(GtkWindowView):
    TITLE = 'Settings'

    def setup(self):
        self.window.set_default_size(300, -1)
        self.window.props.resizable = False

        body = Gtk.Grid(row_spacing=10)
        self.window.add(body)

        settings_body = Gtk.Grid(margin=10)
        body.attach(settings_body, 0, 0, 1, 1)

        settings_body.attach(Header(label='Camera History', margin_bottom=10), 0, 0, 1, 1)

        camera_history_container = Gtk.Grid(margin_left=20, column_spacing=10, row_spacing=10)
        settings_body.attach(camera_history_container, 0, 1, 1, 1)

        self.camera_history_enabled_input = Gtk.CheckButton.new_with_label('Enable camera history'
                                                                           )  # type: Gtk.CheckButton
        camera_history_container.attach(self.camera_history_enabled_input, 0, 0, 1, 1)

        def handle_camera_history_enabled_input_toggled(widget: Gtk.CheckButton):
            data_binding.poke(self, type(self).camera_history_enabled)

            # todo: should connect to camera_history_enabled property change event instead
            self.camera_history_sensitive_group.props.sensitive = self.camera_history_enabled

        self.camera_history_enabled_input.connect('toggled', handle_camera_history_enabled_input_toggled)

        self.camera_history_sensitive_group = Gtk.Grid(column_spacing=10, row_spacing=10, sensitive=False)

        camera_history_location_lbl = Gtk.Label('Location:', halign=Gtk.Align.START)
        self.camera_history_sensitive_group.attach(camera_history_location_lbl, 0, 0, 1, 1)

        self.camera_history_location_input = Gtk.FileChooserButton(action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.camera_history_sensitive_group.attach(self.camera_history_location_input, 1, 0, 1, 1)
        self.camera_history_location_input.connect(
            'selection-changed',
            lambda w: data_binding.poke(self, type(self).camera_history_location)
        )

        camera_history_limit_lbl = Gtk.Label('Max images:', halign=Gtk.Align.START)
        self.camera_history_sensitive_group.attach(camera_history_limit_lbl, 0, 1, 1, 1)

        self.camera_history_limit_input = IntegerEntry(min=-1, width_chars=10)
        self.camera_history_sensitive_group.attach(self.camera_history_limit_input, 1, 1, 1, 1)
        self.camera_history_limit_input.connect(
            'changed',
            lambda w: data_binding.poke(self, type(self).camera_history_limit)
        )

        camera_history_container.attach(self.camera_history_sensitive_group, 0, 1, 1, 1)

        settings_body.attach(Header(label='Constants', margin_top=15, margin_bottom=10), 0, 2, 1, 1)

        constants_container = Gtk.Grid(margin_left=20, column_spacing=10, row_spacing=10)
        settings_body.attach(constants_container, 0, 3, 1, 1)

        gravity_lbl = Gtk.Label('Gravity (ms⁻²):', halign=Gtk.Align.START)
        constants_container.attach(gravity_lbl, 0, 0, 1, 1)

        self.gravity_input = FloatEntry(min=0, width_chars=10)
        constants_container.attach(self.gravity_input, 1, 0, 1, 1)
        self.gravity_input.connect(
            'changed',
            lambda w: data_binding.poke(self, type(self).gravity)
        )

        action_bar = Gtk.ActionBar()
        body.attach(action_bar, 0, 1, 1, 1)

        self.save_btn = Gtk.Button('Save')
        action_bar.pack_end(self.save_btn)
        self.save_btn.connect('clicked', lambda w: self.events['save_btn.on_clicked'].fire())

        self.cancel_btn = Gtk.Button('Cancel')
        action_bar.pack_end(self.cancel_btn)
        self.cancel_btn.connect('clicked', lambda w: self.events['cancel_btn.on_clicked'].fire())

        self.window.show_all()

    @data_binding.property
    def camera_history_enabled(self) -> bool:
        return self.camera_history_enabled_input.props.active

    @camera_history_enabled.setter
    def camera_history_enabled(self, value: bool) -> None:
        self.camera_history_enabled_input.props.active = value

    @data_binding.property
    def camera_history_location(self) -> str:
        return self.camera_history_location_input.get_filename()

    @camera_history_location.setter
    def camera_history_location(self, value: str) -> None:
        print('go set input to', value)
        self.camera_history_location_input.set_filename(value)

    @data_binding.property
    def camera_history_limit(self) -> int:
        return self.camera_history_limit_input.props.value

    @camera_history_limit.setter
    def camera_history_limit(self, value: int) -> None:
        self.camera_history_limit_input.props.value = value

    @data_binding.property
    def gravity(self) -> float:
        return self.gravity_input.props.value

    @gravity.setter
    def gravity(self, value: float) -> None:
        self.gravity_input.props.value = value
