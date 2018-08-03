from opendrop.app3.analysis import IFTAnalysis
from opendrop.app3.ui.iftsetup.scene import IFTSetupScene
from opendrop.app3.ui.mainmenu.scene import MainMenuScene
from opendrop.mvp2.gtk.application import GtkApplication


class OpendropApplication(GtkApplication):
    async def _main(self):
        ift_analysis = IFTAnalysis()
        ift_config_obj = ift_analysis.config

        # main_menu = self.initialise_scene(MainMenuScene)
        main_menu = self.initialise_scene(IFTSetupScene, ift_config_obj)
        # observer_service = ObserverService(imageacquisition.types.get_all_types())
        # main_menu = self.initialise_scene(ObserverChooserScene, observer_service)

        while True:
            resp = await main_menu.on_response

            print("Handling", resp)

            if isinstance(resp, IFTSetupScene.ResponseReturn) or True:
                main_menu.destroy()
                self.quit(resp)
                break
