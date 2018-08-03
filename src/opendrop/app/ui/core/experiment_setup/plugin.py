from abc import abstractmethod
from typing import List, Type

from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup

from .presenter import ExperimentSetupPresenter
from .view import ExperimentSetupView


class ExperimentSetupPlugin:
    def __init__(self, experiment_setup_model: ExperimentSetup, experiment_setup_view: ExperimentSetupView,
                 experiment_setup_presenter: ExperimentSetupPresenter):
        self.experiment_setup_model = experiment_setup_model  # type: ExperimentSetup
        self.experiment_setup_view = experiment_setup_view  # type: T
        self.experiment_setup_presenter = experiment_setup_presenter  # type: ExperimentSetupPresenter

        self._helpers = []  # type: List[ExperimentSetupPlugin]

    def do_setup(self, *args, **kwargs):
        self.experiment_setup_model.events.reconnect_handlers(self, 'experiment_setup_model')

        self.experiment_setup_view.events.reconnect_handlers(self, 'experiment_setup_view')

        self.setup(*args, **kwargs)

    def setup(self, *args, **kwargs):
        pass

    def teardown(self) -> None:
        pass

    def load_helper(self, helper_cls: Type['ExperimentSetupPlugin'], *args, **kwargs):
        helper = helper_cls(self.experiment_setup_model, self.experiment_setup_view, self.experiment_setup_presenter)

        helper.do_setup(*args, **kwargs)

        # Add it to the list of helpers so we hold a reference to it and the helper doesn't get garbage collected
        self._helpers.append(helper)

        return helper

    @classmethod
    @abstractmethod
    def should_load(cls, model: ExperimentSetup) -> bool: pass
