from typing import Optional

from opendrop.app.models.experiments.ift.experiment_notebook import ExperimentNotebook

from opendrop.mvp.Presenter import Presenter
from opendrop.utility.events import handler

from .drop_snapshot.view import DropSnapshotView
from .save_dialog.view import SaveDialogView
from .view import IFTResultsView, DropSnapshotListStoreUpdater


class IFTResultsPresenter(Presenter[ExperimentNotebook, IFTResultsView]):
    def setup(self):
        self.save_dialog = None  # type: Optional[SaveDialogView]

        for i, drop_snapshot in enumerate(self.model.drop_snapshots):
            drop_snapshot_view = self.view.spawn(DropSnapshotView, model=drop_snapshot, child=True)
            drop_snapshot_lsupdater = self.view.add_drop_snapshot(drop_snapshot_view
                                                                  )  # type: DropSnapshotListStoreUpdater

            drop_snapshot_lsupdater.set_frame_num(i)

            def handle_drop_snapshot_status_changed(ds=drop_snapshot, lsupdater=drop_snapshot_lsupdater):
                lsupdater.set_status(ds.status)

            drop_snapshot.events.on_status_changed.connect(handle_drop_snapshot_status_changed, strong_ref=True)
            drop_snapshot.events.on_params_changed.connect(self.update_graphs)
            handle_drop_snapshot_status_changed()

    def update_graphs(self) -> None:
        pad_percent = 0.1

        t = []
        v_ift = []
        v_vol = []
        v_sur = []

        for ds in self.model.drop_snapshots:
            if ds.fit is None:
                continue

            t.append(ds.observation.timestamp)
            v_ift.append(ds.derived.ift)
            v_vol.append(ds.derived.volume)
            v_sur.append(ds.derived.surface_area)

        self.view.set_ift_data(t, v_ift)
        self.view.set_vol_data(t, v_vol)
        self.view.set_sur_data(t, v_sur)

        tlim = (min(t), max(t))

        if tlim[0] == tlim[1]:
            tlim = tlim[0], tlim[0] + 1

        pad = (max(v_ift) - min(v_ift)) * pad_percent
        pad = min(abs(min(v_ift)), pad) or 1
        self.view.set_ift_lims(tlim, (min(v_ift) - pad, max(v_ift) + pad))
        pad = (max(v_vol) - min(v_vol)) * pad_percent
        pad = min(abs(min(v_vol)), pad) or 1
        self.view.set_vol_lims(tlim, (min(v_vol) - pad, max(v_vol) + pad))
        pad = (max(v_sur) - min(v_sur)) * pad_percent
        pad = min(abs(min(v_sur)), pad) or 1
        self.view.set_sur_lims(tlim, (min(v_sur) - pad, max(v_sur) + pad))

    @handler('model', 'on_progress_changed')
    def update_progress(self) -> None:
        self.view.set_progress(self.model.progress)

    @handler('model', 'on_time_remaining_changed')
    def update_time_remaining(self) -> None:
        self.view.set_time_remaining(self.model.time_remaining)

    @handler('model', 'on_time_elapsed_changed')
    def update_time_elapsed(self) -> None:
        self.view.set_time_elapsed(self.model.time_elapsed)

    @handler('view', 'on_back_btn_clicked')
    def handle_back_btn_clicked(self) -> None:
        if self.view.destroyed:
            return

        self.view.spawn(self.view.PREVIOUS)

        self.model.cancel()
        self.view.close()

    @handler('view', 'on_save_btn_clicked')
    def handle_save_btn_clicked(self) -> None:
        if self.save_dialog is not None and not self.save_dialog.destroyed:
            return

        # todo: confirm save even though not 100% fitted yet
        self.save_dialog = self.view.spawn(SaveDialogView, model=self.model.create_save_request(), child=True,
                                           view_opts={'transient_for': self.view, 'modal': True})
