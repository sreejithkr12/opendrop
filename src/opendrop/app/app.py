from opendrop import app
from opendrop.app.models.main_menu import MainMenu
from opendrop.app.ui.main_menu.view import MainMenuView
from opendrop.gtk_specific.GtkApplication import GtkApplication


class OpendropApplication(GtkApplication):
    APPLICATION_ID = 'com.github.jdber1.opendrop'

    PRESENTERS_PKG = app

    def main(self) -> None:
        # todo: allow to spawn and close, without killing app
        # self.spawn(view_cls=SaveDialogView, model=IFTResultsSaveRequest(None))
        # self.spawn(view_cls=SettingsView, model=Settings())
        main_menu = MainMenu()
        self.spawn(view_cls=MainMenuView, model=main_menu) #, model=IFTSetupModel())
