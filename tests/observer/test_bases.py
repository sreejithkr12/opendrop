import asyncio
import time
from typing import Any, Optional
from unittest.mock import Mock

import numpy as np
import pytest
from pytest import raises

from opendrop.observer.bases import ObserverProvider, ObserverType, Observation, ObservationCancelled


def test_stub(): pass


class TestObserverType:
    def setup(self):
        class TestProviderA(ObserverProvider):
            def provide(self, opt1: int, opt2: 'str', opt3: Optional[str] = 'something') -> Any:
                pass

        class TestProviderB(ObserverProvider):
            CONFIG_OPTS = dict(
                opt1={'display': 'Option 1', 'type': int},
                opt2={'display': 'Option 2', 'type': str},
                opt3={'display': 'Option 3', 'type': Optional[str]}
            )

            def provide(self, opt1: int, opt2: 'str', opt3: Optional[str] = 'something') -> Any:
                pass

        self.provider_a = TestProviderA
        self.provider_b = TestProviderB

        self.observer_type_a = ObserverType('TestA', TestProviderA())
        self.observer_type_b = ObserverType('TestB', TestProviderB())

    def test_config_opts(self):
        assert self.observer_type_a.config_opts == dict(
            opt1={'display': 'opt1', 'type': int},
            opt2={'display': 'opt2', 'type': str},
            opt3={'display': 'opt3', 'type': Optional[str]}
        )

        assert self.observer_type_b.config_opts == self.provider_b.CONFIG_OPTS


class TestObservation:
    def setup(self):
        self.o = Observation()
        self.image = np.array([[255, 127, 0]], dtype=np.uint8)

    def test_load(self):
        assert not self.o.ready

        self.o.load(self.image)

        assert self.o.ready

    def test_double_load(self):
        self.o.load(self.image)

        # Shouldn't be able to load an image into an `Observation` that is already 'loaded'.
        with pytest.raises(ValueError):
            self.o.load(self.image)

    @pytest.mark.asyncio
    async def test_await(self):
        EPSILON = 0.01
        WAIT = 0.1

        asyncio.get_event_loop().call_later(WAIT, self.o.load, self.image)

        start = time.time()

        image = await self.o

        # Try awaiting again, to make sure it works more than once
        image = await self.o

        assert (image == self.image).all()
        assert abs(time.time() - start - WAIT) < EPSILON

    @pytest.mark.asyncio
    async def test_on_ready_event(self):
        cb = Mock()

        self.o.events.on_ready.connect(cb)

        asyncio.get_event_loop().call_soon(self.o.load, self.image)

        await asyncio.sleep(0.001)

        cb.assert_called_once_with(self.image)

    def test_image(self):
        self.o.load(self.image)

        assert (self.o.image == self.image).all()

    def test_default_timestamp(self):
        EPSILON = 0.01

        self.o.load(self.image)

        assert abs(self.o.timestamp - time.time()) < EPSILON

    def test_defined_timestamp(self):
        TIMESTAMP = 123

        self.o.load(self.image, TIMESTAMP)

        assert self.o.timestamp == TIMESTAMP

    def test_cancel(self):
        assert not self.o.cancelled

        self.o.cancel()

        assert self.o.cancelled

    @pytest.mark.asyncio
    async def test_await_cancelled(self):
        async def cancel_observation(delay=0.0):
            await asyncio.sleep(delay)
            self.o.cancel()

        asyncio.get_event_loop().create_task(cancel_observation(0.5))

        with raises(ObservationCancelled):
            await asyncio.wait_for(self.o, 1)

    @pytest.mark.asyncio
    async def test_await_already_cancelled(self):
        self.o.load(self.image)
        self.o.cancel()

        with raises(ObservationCancelled):
            await self.o
