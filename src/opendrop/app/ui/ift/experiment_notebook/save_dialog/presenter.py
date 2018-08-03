from opendrop.app.models.experiments.ift.experiment_notebook import ExperimentSaveRequest
from opendrop.mvp.Presenter import Presenter
from opendrop.utility import data_binding
from opendrop.utility.events import handler

from .view import SaveDialogView


class SaveDialogPresenter(Presenter[ExperimentSaveRequest, SaveDialogView]):
    def setup(self):
        routes = [
            *data_binding.Route.both(type(self.model).save_parent_dir, type(self.view).save_parent_dir, to_b=str),
            *data_binding.Route.both(type(self.model).save_name, type(self.view).save_name),
            *data_binding.Route.both(type(self.model).graph_dpi, type(self.view).graph_dpi),
        ]

        data_binding.bind(self.model, self.view, routes)
        data_binding.poke(self.model)

    # todo: if no drops to save, then disable the save button?
    # todo: if drops not all complete, tell user with dialog
    @handler('view', 'on_save_btn_clicked')
    def handle_view_save_btn_clicked(self):
        if self.model.validate():
            return

        self.model.submit()
        self.view.close()
