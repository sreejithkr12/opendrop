from typing import Optional, List

from opendrop.app.models.experiments.core.experiment_setup import ExperimentSetup
from opendrop.mvp.Presenter import Presenter
from opendrop.observer.bases import ObserverPreview
from opendrop.utility.events import handler, EventSource
from opendrop.utility.events.events import HasEvents

from .observer_chooser_dialog.view import ObserverChooserDialogView
from .view import ExperimentSetupView


class LockChild(HasEvents):
    def __init__(self, pool: 'LockPool') -> None:
        self.events = EventSource()

        self._pool = pool  # type: LockPool

    def acquire(self) -> None:
        if self.active:
            return

        self._pool._set_active_lock(lock=self)

        self.events.on_acquired.fire()

    def release(self):
        if not self.active:
            return

        self._pool._release_lock(lock=self)

        self.events.on_released.fire()

    @property
    def active(self):
        return self._pool._is_lock_active(lock=self)


class LockPool:
    def __init__(self):
        self._active_lock = None  # type: Optional[LockChild]

    def get(self) -> LockChild:
        return LockChild(pool=self)

    def _set_active_lock(self, lock: LockChild) -> None:
        if self.active_lock is not None:
            self.active_lock.release()

        self.active_lock = lock

    def _is_lock_active(self, lock: LockChild) -> bool:
        return self.active_lock == lock

    def _release_lock(self, lock: LockChild) -> None:
        assert self._is_lock_active(lock)

        self.active_lock = None

    @property
    def active_lock(self) -> LockChild:
        return self._active_lock

    @active_lock.setter
    def active_lock(self, value: Optional[LockChild]) -> None:
        self._active_lock = value

    @property
    def busy(self):
        return self.active_lock is not None


class ExperimentSetupPresenter(Presenter[ExperimentSetup, ExperimentSetupView]):
    IGNORE = True

    def setup(self) -> None:
        # Attributes
        #  public
        self.activity_locks = LockPool()

        #  private
        self._active_preview = None  # type: Optional[ObserverPreview]
        self._observer_chosen = False  # type: bool
        self._plugins = []  # type: List[ExperimentSetupPlugin]

        self.model.postproc.clear()

        # todo: support restoring from model if imageacquisition already chosen
        if self.model.observer is None:
            self.prompt_user_to_choose_observer()
        else:
            self.handle_observer_changed()

    def prompt_user_to_choose_observer(self) -> None:
        v = self.view.spawn(ObserverChooserDialogView, model=self.model, child=True,
                            view_opts={'transient_for': self.view, 'modal': True})  # type: ObserverChooserDialogView

        v.events.on_destroy.connect(self._handle_observer_chooser_on_submit, once=True)

    def _handle_observer_chooser_on_submit(self) -> None:
        if self.model.observer is None:
            self.view.spawn(self.view.PREVIOUS)
            self.view.close()

            return

    def clear_active_preview(self):
        if self.active_preview is not None:
            print('close active preivew')
            self.active_preview.close()

            self.active_preview = None

    @property
    def active_preview(self) -> Optional[ObserverPreview]:
        return self._active_preview

    @active_preview.setter
    def active_preview(self, value: Optional[ObserverPreview]) -> None:
        self._active_preview = value

        if not self.view.destroyed:
            self.view.set_viewer_preview(value)

    @handler('model', 'on_observer_changed')
    def handle_observer_changed(self) -> None:
        self.clear_active_preview()

        self.reload_plugins()

        if self.model.observer is not None:
            self.active_preview = self.model.observer.preview()

    @handler('view', 'cancel_btn.on_clicked')
    def handle_cancel_btn_clicked(self) -> None:
        self.view.spawn(self.view.PREVIOUS)
        self.view.close()

    def clear_plugins(self) -> None:
        for p in self._plugins:
            p.teardown()

        self._plugins = []

    def load_plugins(self) -> None:
        from . import plugins

        to_load = filter(
            lambda p: p.should_load(self.model), plugins.get_plugins()
        )

        for plugin_cls in to_load:
            plugin = plugin_cls(experiment_setup_model=self.model,
                                experiment_setup_view=self.view,
                                experiment_setup_presenter=self)

            plugin.do_setup()

            self._plugins.append(plugin)

    def reload_plugins(self) -> None:
        self.clear_plugins()
        self.load_plugins()

    def teardown(self) -> None:
        for p in list(self._plugins):
            self._plugins.remove(p)

        self.clear_active_preview()
