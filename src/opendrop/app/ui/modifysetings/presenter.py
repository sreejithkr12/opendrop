from opendrop.app.models.modifysettings import ModifySettings
from opendrop.app.ui.modifysetings.view import ModifySettingsView
from opendrop.mvp.Presenter import Presenter
from opendrop.utility import data_binding
from opendrop.utility.events import handler


class ModifySettingsPresenter(Presenter[ModifySettings, ModifySettingsView]):
    def setup(self):
        routes = [
            *data_binding.Route.both(type(self.model).camera_history_enabled, type(self.view).camera_history_enabled),
            *data_binding.Route.both(type(self.model).camera_history_location, type(self.view).camera_history_location),
            *data_binding.Route.both(type(self.model).camera_history_limit, type(self.view).camera_history_limit),
            *data_binding.Route.both(type(self.model).gravity, type(self.view).gravity),
        ]

        data_binding.bind(self.model, self.view, routes)
        data_binding.poke(self.model)

    @handler('view', 'save_btn.on_clicked')
    def handle_view_save_btn_clicked(self) -> None:
        if self.model.validate():
            return

        self.model.save()
        self.close_view()

    @handler('view', 'cancel_btn.on_clicked')
    def close_view(self) -> None:
        self.view.close()
