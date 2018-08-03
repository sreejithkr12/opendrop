from unittest.mock import Mock

from opendrop.app.ui.core.experiment_setup.presenter import LockPool


def test_stub(): pass


class TestLockPool:
    def setup(self):
        self.lock_pool = LockPool()

    def test_get(self):
        lock = self.lock_pool.get()

    def test_busy_and_lock_child_release(self):
        assert not self.lock_pool.busy

        lock1 = self.lock_pool.get()

        lock1.acquire()

        assert self.lock_pool.busy

        lock1.release()

        assert not self.lock_pool.busy

        lock2 = self.lock_pool.get()

        lock2.acquire()

        assert self.lock_pool.busy

        lock1.release()

        assert self.lock_pool.busy

    def test_acquire_while_busy(self):
        lock1 = self.lock_pool.get()
        lock2 = self.lock_pool.get()

        handle_lock1_release = Mock()
        lock1.events.on_released.connect(handle_lock1_release, immediate=True)

        lock1.acquire()
        lock2.acquire()

        handle_lock1_release.assert_called_once_with()


class TestLockChild:
    def setup(self):
        self.lock_pool = LockPool()
        self.lock_child = self.lock_pool.get()

    def test_acquire_and_on_acquired_event(self):
        handle_acquire = Mock()
        handle_release = Mock()

        self.lock_child.events.on_acquired.connect(handle_acquire, immediate=True)
        self.lock_child.events.on_released.connect(handle_release, immediate=True)

        self.lock_child.acquire()

        handle_acquire.assert_called_once_with()
        handle_release.assert_not_called()

        # Acquiring a lock shouldn't release the current lock if they are the same, i.e. acquiring the same lock twice
        # shouldn't do anything
        self.lock_child.acquire()

        handle_acquire.assert_called_once_with()
        handle_release.assert_not_called()

    def test_on_released_event(self):
        cb = Mock()

        self.lock_child.acquire()

        self.lock_child.events.on_released.connect(cb, immediate=True)

        self.lock_child.release()

        cb.assert_called_once_with()

        # Releasing when the lock is already released shouldn't fire the on_released event again
        self.lock_child.release()

        cb.assert_called_once_with()

    def test_active(self):
        assert not self.lock_child.active

        self.lock_child.acquire()

        assert self.lock_child.active

        self.lock_child.release()

        assert not self.lock_child.active
