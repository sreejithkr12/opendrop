# TODO: improve cpu performance by not having to iterate through the asyncio event loop all the time. This would be done
# by possibly having to write a custom event loop class.

import asyncio

import functools

from typing import Any

import time
from gi.repository import GObject


STEP_SLEEP = 0.005


class GtkHookLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """An asyncio event loop policy that allows the asyncio event loop to run alongside the Gtk event loop. Each time
    the Gtk event loop idles, one 'iteration' of the asyncio event loop is made.
    """
    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        loop = WrappedLoopRunOnGLoop(loop)

        super().set_event_loop(loop)

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        loop = super().get_event_loop()  # type: asyncio.AbstractEventLoop

        assert isinstance(loop, WrappedLoopRunOnGLoop)

        return loop


class WrappedLoopRunOnGLoopMethods:
    alive = False  # type: bool

    def run_forever(self) -> None:
        if self.alive:
            raise RuntimeError('This event loop is already running')

        self.alive = True
        GObject.idle_add(self.step)

    def stop(self) -> None:
        self.alive = False
        self.step()

    def run_once(self) -> None:
        # This pairing of 'arrange a call to stop' and 'run_forever' is used to iterate through the event loop once
        self.target.stop()

        try:
            self.target.run_forever()
        except RuntimeError:
            pass

        # Sleep for a bit so CPU usage isn't 100%
        time.sleep(STEP_SLEEP)

    def step(self) -> None:
        if self.is_closed():
            return

        if self.alive:
            self.call_soon(GObject.idle_add, self.step)
            self.run_once()
        else:
            self.target.stop()


class WrappedLoopRunOnGLoop(asyncio.AbstractEventLoop):
    def __init__(self, target: asyncio.AbstractEventLoop) -> None:
        self.target = target  # type: asyncio.AbstractEventLoop
        self.alive = False  # type: bool

    def __getattribute__(self, name: str) -> Any:
        if name == "alive" or name == "target":
            return object.__getattribute__(self, name)

        try:
            return functools.partial(getattr(WrappedLoopRunOnGLoopMethods, name), self)
        except AttributeError:
            return getattr(self.target, name)
