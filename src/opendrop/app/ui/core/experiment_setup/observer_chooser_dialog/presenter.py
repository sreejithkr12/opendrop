from typing import Any, MutableMapping, NewType

from opendrop.mvp.Presenter import Presenter
from opendrop.utility.events import handler
from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup
from opendrop.app.models.experiments.core.experiment_setup import ChangeObserverRequest

from .observer_config.base_config.view import ObserverConfigView
from .view import ObserverChooserDialogView

# Avoid importing from opendrop.imageacquisition.bases since we don't actually need to interact with ObserverType, just pass it
# around as an opaque data type
ObserverType = NewType('ObserverType', Any)


class CameraChooserDialogPresenter(Presenter[ExperimentSetup, ObserverChooserDialogView]):
    def setup(self):
        self.config_requests = {}  # type: MutableMapping[Any, ChangeObserverRequest]

        for i, o_type in enumerate(sorted(self.model.observer_types.get_types(), key=lambda ot: ot.display)):
            config_id = str(i)  # type: str

            config_request = self.model.change_observer()  # type: ChangeObserverRequest
            config_view_cls = ObserverConfigView.get_view_for(o_type)
            config_view = self.view.spawn(config_view_cls, model=config_request, child=True)

            self.config_requests[config_id] = config_request
            self.view.add_observer_type(id=config_id, name=o_type.display, config_view=config_view)

        self.view.observer_type_id = '0'

    # @handler('view', 'on_type_combo_changed', immediate=True)
    # def handle_type_combo_changed(self, active_id: str):
    #     self.config_request.reset()

    @handler('view', 'on_user_submit_button_clicked')
    def handle_submit_clicked(self):
        active_config_request = self.config_requests[self.view.observer_type_id]
        active_config_request.submit()
        self.view.close()

    @handler('view', 'on_user_cancel_button_clicked')
    def handle_cancel_clicked(self):
        self.view.close()
