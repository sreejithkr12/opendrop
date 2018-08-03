from opendrop.app.models.main_menu import MainMenu
from opendrop.app.ui.modifysetings.view import ModifySettingsView
from opendrop.mvp.Presenter import Presenter
from opendrop.utility.events import handler

from ..ift.experiment_setup.view import IFTSetupView
from .view import MainMenuView


class MainMenuPresenter(Presenter[MainMenu, MainMenuView]):
    def setup(self):
        self.view.set_version(self.model.ABOUT.version)
        self.view.set_version_name(self.model.ABOUT.version_name)

        self.view.set_about_info(
            self.model.ABOUT.program_name,
            self.model.ABOUT.website,
            self.model.ABOUT.comments,
            self.model.ABOUT.authors
        )

    @handler('view', 'ift_btn.on_clicked')
    def handle_view_ift_btn_on_clicked(self) -> None:
        ift_experiment_setup = self.model.new_ift_experiment()

        self.view.spawn(IFTSetupView, model=ift_experiment_setup)
        self.view.close()

    @handler('view', 'settings_btn.on_clicked')
    def handle_view_settings_btn_clicked(self) -> None:
        self.view.spawn(ModifySettingsView, model=self.model.modify_settings(), child=True,
                        view_opts={'transient_for': self.view, 'modal': True})

    @handler('view', 'about_btn.on_clicked')
    def handle_view_about_btn_on_clicked(self) -> None:
        self.view.show_about_window()
