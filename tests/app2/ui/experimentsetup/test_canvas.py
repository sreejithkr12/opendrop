from unittest.mock import Mock

import numpy as np
from pytest import raises

from opendrop.app2.ui.experimentsetup.canvas import CanvasLayer, CanvasContext, Canvas

BLACK = [0, 0, 0]
RED = [255, 0, 0]
GREEN = [0, 255, 0]
BLUE = [0, 0, 255]
YELLOW = [255, 255, 0]


def test_add_layer_dirties():
    checkpoints = []

    class MyLayer(CanvasLayer):
        def draw(self, ctx: CanvasContext) -> None:
            checkpoints.append(('draw', ctx.viewport.shape[1::-1], ctx.artboard.shape[1::-1], ctx.artboard_extents))

    my_canvas = Canvas((10, 15))
    my_canvas_changed_cb = Mock()
    my_canvas.on_changed.connect(my_canvas_changed_cb, immediate=True)

    assert my_canvas_changed_cb.call_count == 0

    my_layer = MyLayer()
    my_canvas.add_layer(my_layer, 0)

    assert my_canvas_changed_cb.call_count == 1

    assert checkpoints == [
        ('draw', (10, 15), (10, 15), (0, 0, 10, 15))
    ]


def test_change_viewport_pos_and_artboard_pos_and_size_dirties():
    checkpoints = []

    class MyLayer(CanvasLayer):
        def draw(self, ctx: CanvasContext) -> None:
            checkpoints.append(('draw', ctx.viewport.shape[1::-1], ctx.artboard.shape[1::-1], ctx.artboard_extents))

    my_canvas = Canvas((10, 15))
    my_canvas_changed_cb = Mock()
    my_canvas.on_changed.connect(my_canvas_changed_cb, immediate=True)
    my_layer = MyLayer()
    my_canvas.add_layer(my_layer, 0)

    # Reset checkpoints and my_canvas_changed_cb since `add_layer()` would have modified them.
    my_canvas_changed_cb.reset_mock()
    checkpoints = []

    my_canvas.viewport_size = (20, 25)
    assert my_canvas_changed_cb.call_count == 1
    my_canvas.artboard_pos = (2, 3)
    assert my_canvas_changed_cb.call_count == 2
    my_canvas.artboard_size = (11, 12)
    assert my_canvas_changed_cb.call_count == 3

    assert checkpoints == [
        ('draw', (20, 25), (10, 15), (0, 0, 10, 15)),
        ('draw', (20, 25), (10, 15), (2, 3, 12, 18)),
        ('draw', (20, 25), (11, 12), (2, 3, 13, 15))
    ]


def test_single_layer_viewport_draw_and_dirtied():
    checkpoints = []

    class MyLayer(CanvasLayer):
        def draw(self, ctx: CanvasContext) -> None:
            checkpoints.append(('draw', ctx.viewport.shape[1::-1], ctx.artboard.shape[1::-1], ctx.artboard_extents))
            ctx.viewport[0, 0] = RED

    my_canvas = Canvas((10, 15))
    my_canvas_changed_cb = Mock()
    my_canvas.on_changed.connect(my_canvas_changed_cb, immediate=True)
    my_layer = MyLayer()
    my_canvas.add_layer(my_layer, 0)

    checkpoints = []
    my_canvas_changed_cb.reset_mock()

    my_layer.dirtied()

    my_canvas_changed_cb.assert_called_once_with()

    assert checkpoints == [
        ('draw', (10, 15), (10, 15), (0, 0, 10, 15))
    ]

    target_buffer = np.zeros((15, 10, 3))
    target_buffer[0, 0] = RED

    assert (my_canvas.buffer == target_buffer).all()


def test_single_layer_artboard_draw():
    checkpoints = []

    class MyLayer(CanvasLayer):
        def draw(self, ctx: CanvasContext) -> None:
            checkpoints.append(('draw', ctx.artboard.shape[1::-1], ctx.artboard_extents))
            ctx.artboard[1, 2] = RED
            ctx.artboard[-1, -1] = GREEN

    my_canvas = Canvas((10, 15))
    my_canvas.artboard_pos = (4, 5)
    my_canvas.artboard_size = (4, 6)

    my_layer = MyLayer()
    my_canvas.add_layer(my_layer, 0)

    checkpoints = []

    my_layer.dirtied()

    assert checkpoints == [
        ('draw', (4, 6), (4, 5, 8, 11))
    ]

    target_buffer = np.zeros((15, 10, 3))
    target_buffer[:] = BLACK
    target_buffer[6, 6] = RED
    target_buffer[10, 7] = GREEN

    assert (my_canvas.buffer == target_buffer).all()


def test_artboard_over_extents():
    checkpoints = []

    class MyLayer(CanvasLayer):
        def draw(self, ctx: CanvasContext) -> None:
            checkpoints.append(('draw', ctx.artboard.shape[1::-1], ctx.artboard_extents))
            ctx.artboard[0, 0] = RED
            ctx.artboard[-1, -1] = GREEN

    my_canvas = Canvas((10, 10))
    my_canvas.artboard_pos = (4, 5)
    my_canvas.artboard_size = (20, 25)

    my_layer = MyLayer()
    my_canvas.add_layer(my_layer, 0)

    checkpoints = []

    target_buffer = np.zeros((10, 10, 3))

    # Dirty the canvas, draw() is invoked
    my_layer.dirtied()

    target_buffer[:] = BLACK
    target_buffer[5, 4] = RED
    target_buffer[-1, -1] = GREEN
    assert (my_canvas.buffer == target_buffer).all()

    # Dirty the canvas (by changing artboard_pos), draw() is invoked
    my_canvas.artboard_pos = (-19, -24)

    target_buffer[:] = BLACK
    target_buffer[0, 0] = GREEN
    assert (my_canvas.buffer == target_buffer).all()

    assert checkpoints == [
        ('draw', (6, 5), (4, 5, 24, 30)),
        ('draw', (1, 1), (-19, -24, 1, 1))
    ]


def test_multi_layer_draw_and_z_index():
    checkpoints = []

    class MyLayer(CanvasLayer):
        def __init__(self, name, col):
            super().__init__()
            self.name = name
            self.col = col

        def draw(self, ctx: CanvasContext) -> None:
            checkpoints.append(
                ('{}.draw'.format(self.name), ctx.viewport[3, 3].tolist(), ctx.artboard[0, 0].tolist())
            )
            ctx.artboard[0, 0] = self.col

    my_canvas = Canvas((10, 10))
    my_canvas.artboard_pos = (3, 3)

    my_layer0 = MyLayer('red', RED)
    my_canvas.add_layer(my_layer0, 0)

    my_layer1 = MyLayer('green', GREEN)
    my_canvas.add_layer(my_layer1, 1)

    checkpoints = []

    target_buffer = np.zeros((10, 10, 3))
    target_buffer[:] = BLACK

    # Dirty the canvas
    my_layer0.dirtied()

    assert checkpoints == [
        ('red.draw', BLACK, BLACK),
        ('green.draw', RED, RED)
    ]


def test_remove_layer():
    checkpoints = []

    class MyLayer(CanvasLayer):
        def __init__(self, name, col):
            super().__init__()
            self.name = name
            self.col = col

        def draw(self, ctx: CanvasContext) -> None:
            checkpoints.append(
                ('{}.draw'.format(self.name), ctx.viewport[3, 3].tolist(), ctx.artboard[0, 0].tolist())
            )
            ctx.artboard[0, 0] = self.col

    my_canvas = Canvas((10, 10))
    my_canvas.artboard_pos = (3, 3)
    my_canvas_changed_cb = Mock()
    my_canvas.on_changed.connect(my_canvas_changed_cb, immediate=True)

    my_layer0 = MyLayer('red', RED)
    my_canvas.add_layer(my_layer0, 0)

    my_layer1 = MyLayer('green', GREEN)
    my_canvas.add_layer(my_layer1, 1)

    my_layer2 = MyLayer('blue', BLUE)
    my_canvas.add_layer(my_layer2, 2)

    my_layer3 = MyLayer('yellow', YELLOW)
    my_canvas.add_layer(my_layer3, 3)

    # Reset checkpoints
    checkpoints = []
    my_canvas_changed_cb.reset_mock()

    # Remove layer should fire the `on_changed` event and redraw the buffer
    my_canvas.remove_layer(my_layer1)

    assert my_canvas_changed_cb.call_count == 1
    assert checkpoints == [
        ('red.draw', BLACK, BLACK),
        ('blue.draw', RED, RED),
        ('yellow.draw', BLUE, BLUE)
    ]

    checkpoints = []
    my_canvas_changed_cb.reset_mock()

    # Layer removed, shouldn't affect the canvas
    my_layer1.dirtied()

    assert checkpoints == []

    # Layer still exists, should dirty the canvas
    my_layer0.dirtied()

    assert checkpoints == [
        ('red.draw', BLACK, BLACK),
        ('blue.draw', RED, RED),
        ('yellow.draw', BLUE, BLUE)
    ]


def test_set_viewport_artboard_size_less_than_1():
    invalid_sizes = ((-4, -2), (4, -3), (-3, 4))

    for size in invalid_sizes:
        with raises(ValueError):
            Canvas(size)

    my_canvas = Canvas((10, 10))

    for size in invalid_sizes:
        with raises(ValueError):
            my_canvas.artboard_size = size
