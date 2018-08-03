from opendrop.app.models.experiments.ift.experiment_setup import IFTExperimentSetup
from opendrop.mvp.Presenter import Presenter
from opendrop.utility.events import handler
from opendrop.app.ui.ift.experiment_notebook.view import IFTResultsView
from opendrop.app.ui.core.experiment_setup.presenter import ExperimentSetupPresenter

from .view import IFTSetupView


class IFTSetupPresenter(ExperimentSetupPresenter, Presenter[IFTExperimentSetup, IFTSetupView]):
    IGNORE = False

    def setup(self):
        super().setup()

    @handler('view', 'begin_btn.on_clicked')
    def handle_begin_btn_clicked(self) -> None:
        errors = self.model.validate()

        if errors:
            for v in errors.values():
                print(v)

            return

        results = self.model.start_experiment()

        self.view.spawn(view_cls=IFTResultsView, model=results)
        self.view.close()
