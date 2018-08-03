from enum import Enum
from numbers import Number

import cv2
from abc import abstractmethod
from collections import namedtuple
from typing import Tuple, List, Optional, Union

import numpy as np

from opendrop.observer.bases import ObserverPreview
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindable, AtomicBindableAdapter
from opendrop.utility.events import Event, EventConnection
from opendrop.utility.misc import slice_view, Rect

CHANNELS = 3

CanvasLayerContainer = namedtuple('CanvasLayerContainer', ('layer', 'z_index', 'event_conns'))


class ArtboardLayoutType(Enum):
    FREE = 0
    FILL = 1
    FIT = 2


class CanvasContext:
    def __init__(self, viewport: np.ndarray, artboard: np.ndarray, artboard_rect: Rect[int]):
        self.viewport = viewport
        self.artboard = artboard
        self.artboard_rect = artboard_rect

        viewport_size = viewport.shape[1::-1]
        visible_xy = np.array([-artboard_rect.x, -artboard_rect.y]).clip(min=0)
        self.artboard_visible_rect = Rect(x=visible_xy[0], y=visible_xy[1], w=viewport_size[0], h=viewport_size[1])

# todo: implement freeze() and thaw() which will prevent on_changed from being emitted while frozen so multiple changes
#       can be made to viewport pos, artboard pos/size without alerting event handlers.
class Canvas:
    def __init__(self, size: Tuple[int, int]):
        self.on_changed = Event()  # emits: ()

        self._buffer = np.zeros(shape=(1, 1, CHANNELS))  # type: np.ndarray
        self._layers = []  # type: List[CanvasLayerContainer]
        self._artboard = None  # type: Optional[CanvasArtboard]
        self._artboard_event_conns = []  # type: List[EventConnection]

        self._viewport_size = (1, 1)
        self._artboard_pos = (0, 0)
        self._artboard_scale = 1.0  # type: Number
        self._artboard_layout = ArtboardLayoutType.FREE  # type: Optional[ArtboardLayoutType]

        self.bn_viewport_size = AtomicBindableAdapter(
            getter=self._raw_get_viewport_size,
            setter=self._raw_set_viewport_size
        )
        self.bn_artboard_pos = AtomicBindableAdapter(
            getter=self._raw_get_artboard_pos,
            setter=self._raw_set_artboard_pos
        )
        self.bn_artboard_scale = AtomicBindableAdapter(
            getter=self._raw_get_artboard_scale,
            setter=self._raw_set_artboard_scale
        )

        self.bn_artboard_layout = AtomicBindableAdapter(
            getter=self._raw_get_artboard_layout,
            setter=self._raw_set_artboard_layout
        )

        self.viewport_size = size

    def add_layer(self, layer: 'CanvasLayer', z_index: int) -> None:
        event_conns = [
            layer.on_dirtied.connect(self._redraw_buffer, immediate=True)
        ]

        ctn = CanvasLayerContainer(layer, z_index, event_conns)
        self._layers.append(ctn)
        self._layers.sort(key=lambda c: c.z_index)
        self._redraw_buffer()

    def remove_layer(self, layer: 'CanvasLayer') -> None:
        for ctn in self._layers:
            if ctn.layer == layer: break
        else:
            raise ValueError('Could not find layer `{}` to remove'.format(layer))

        for conn in ctn.event_conns:
            conn.disconnect()

        # Removing an item should leave the layers list sorted.
        self._layers.remove(ctn)
        self._redraw_buffer()

    def _changed(self) -> None:
        self.on_changed.fire()

    def _recreate_buffer(self) -> None:
        self._buffer = np.zeros(shape=self.viewport_size[::-1] + (3,))
        self._redraw_buffer()

    def _redraw_buffer(self) -> None:
        self.buffer[:] = [220, 220, 220]
        # self.artboard_buffer[:] = [0, 0, 0]

        drawables = tuple(layer for (layer, *_) in self._layers)

        if self._artboard is not None:
            drawables = (self._artboard,) + drawables

        for layer in drawables:
            layer.draw(self._create_context())

        self._changed()

    def _create_context(self) -> CanvasContext:
        return CanvasContext(
            viewport=self.buffer,
            artboard=self.artboard_buffer,
            artboard_rect=self.artboard_draw_rect
        )

    def _raw_get_viewport_size(self) -> Tuple[int, int]:
        return self._viewport_size

    def _raw_set_viewport_size(self, new_size: Tuple[int, int]) -> None:
        if new_size[0] < 0 or new_size[1] < 0:
            raise ValueError(
                "Viewport size can't have negative values, tried to be set with {}"
                    .format(new_size)
            )

        self._viewport_size = new_size
        self._recreate_buffer()

    def _raw_get_artboard_scale(self) -> Number:
        return self._artboard_scale

    def _raw_set_artboard_scale(self, new_scale: Number) -> None:
        if new_scale < 0:
            raise ValueError(
                "Artboard scale can't be negative, tried to be set with {}"
                    .format(new_scale)
            )

        self._artboard_scale = new_scale
        self._redraw_buffer()

    def _raw_get_artboard_pos(self) -> Tuple[int, int]:
        return self._artboard_pos

    def _raw_set_artboard_pos(self, new_pos: Tuple[int, int]) -> None:
        self._artboard_pos = new_pos
        self._redraw_buffer()

    def _raw_get_artboard_layout(self) -> Optional[ArtboardLayoutType]:
        return self._artboard_layout

    def _raw_set_artboard_layout(self, value: Optional[ArtboardLayoutType]) -> None:
        self._artboard_layout = value
        self._redraw_buffer()

    @property
    def artboard(self) -> 'CanvasArtboard':
        return self._artboard

    @artboard.setter
    def artboard(self, new_artboard: 'CanvasArtboard') -> None:
        # todo: test set to none dirties
        if self._artboard is not None:
            for conn in self._artboard_event_conns:
                conn.disconnect()

        self._artboard = new_artboard
        self._artboard_event_conns = []

        if new_artboard is not None:
            self._artboard_event_conns += [
                new_artboard.bn_size.on_changed.connect(self._redraw_buffer, immediate=True)
            ]

        self._redraw_buffer()

    @AtomicBindable.property_adapter
    def viewport_size(self) -> AtomicBindable[Tuple[int, int]]:
        return self.bn_viewport_size

    @AtomicBindable.property_adapter
    def artboard_pos(self) -> AtomicBindable[Tuple[int, int]]:
        return self.bn_artboard_pos

    @AtomicBindable.property_adapter
    def artboard_scale(self) -> AtomicBindable[float]:
        return self.bn_artboard_scale

    @AtomicBindable.property_adapter
    def artboard_layout(self) -> AtomicBindable[Optional[ArtboardLayoutType]]:
        return self.bn_artboard_layout

    @property
    def artboard_draw_pos(self) -> Tuple[int, int]:
        if self._artboard_layout is ArtboardLayoutType.FREE:
            draw_pos = self.artboard_pos
        elif self._artboard_layout is ArtboardLayoutType.FILL or self._artboard_layout is ArtboardLayoutType.FIT:
            draw_pos = (int(self.viewport_size[0]/2 - self.artboard_draw_size[0]/2),
                        int(self.viewport_size[1]/2 - self.artboard_draw_size[1]/2))
        else:
            raise ValueError("Unknown artboard layout type `{}`".format(self._artboard_layout))

        return draw_pos

    @property
    def artboard_draw_size(self) -> Tuple[int, int]:
        if self._artboard is None:
            return 0, 0

        artboard_size = self._artboard.size

        if self._artboard_layout is ArtboardLayoutType.FREE:
            artboard_draw_size = (int(self.artboard_scale * artboard_size[0]),
                                    int(self.artboard_scale * artboard_size[1]))
        elif self._artboard_layout is ArtboardLayoutType.FIT or self._artboard_layout is ArtboardLayoutType.FILL:
            artboard_aspect = artboard_size[0] / artboard_size[1]

            viewport_size = self.viewport_size
            viewport_aspect = viewport_size[0] / viewport_size[1]

            if self._artboard_layout is ArtboardLayoutType.FILL and (viewport_aspect > artboard_aspect)\
            or self._artboard_layout is ArtboardLayoutType.FIT  and (viewport_aspect <= artboard_aspect):
                artboard_draw_size = (viewport_size[0], int(viewport_size[0] * artboard_size[1]/artboard_size[0]))
            else:
                artboard_draw_size = (int(viewport_size[1] * artboard_size[0]/artboard_size[1]), viewport_size[1])
        else:
            raise ValueError("Unknown artboard layout type `{}`".format(self._artboard_layout))

        return artboard_draw_size

    @property
    def artboard_draw_rect(self) -> Rect[int]:
        """Rect(x0, y0, x1, y1), (x1-1, y1-1) is the bottom-right most pixel coordinate."""
        draw_pos = self.artboard_draw_pos
        draw_size = self.artboard_draw_size
        return Rect(x=draw_pos[0], y=draw_pos[1], w=draw_size[0], h=draw_size[1])

    @property
    def buffer(self) -> np.ndarray:
        return self._buffer

    @property
    def artboard_buffer(self) -> np.ndarray:
        artboard_row_col_start = np.array((self.artboard_draw_rect.y0, self.artboard_draw_rect.x0))
        artboard_row_col_stop = np.array((self.artboard_draw_rect.y1, self.artboard_draw_rect.x1))

        artboard_slice_start = artboard_row_col_start.clip(min=[0, 0]).tolist() + [0]
        artboard_slice_stop = artboard_row_col_stop.clip(max=self.viewport_size[::-1]).tolist() + [CHANNELS]

        return slice_view(self.buffer, artboard_slice_start, artboard_slice_stop)


class CanvasLayer:
    def __init__(self):
        self.on_dirtied = Event()  # emits: ()

    @abstractmethod
    def draw(self, ctx: CanvasContext) -> None:
        pass

    def dirtied(self) -> None:
        self.on_dirtied.fire()


class CanvasArtboard(CanvasLayer):
    def __init__(self, size: Tuple[int, int] = (0, 0)):
        super().__init__()
        self.bn_size = AtomicBindableVar(size)

    @AtomicBindable.property_adapter
    def size(self) -> AtomicBindable[Tuple[int, int]]: return self.bn_size


class ObserverPreviewCanvasArtboard(CanvasArtboard):
    def __init__(self, preview: ObserverPreview, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._preview = preview
        preview.on_changed.connect(self._update_size, immediate=True)
        self._update_size()

    def draw(self, ctx: CanvasContext) -> None:
        rect = ctx.artboard_rect
        if rect.w == 0 or rect.h == 0:
            return

        preview_buffer = self._preview.buffer
        resized_buffer = cv2.resize(preview_buffer, dsize=(ctx.artboard_rect.w, ctx.artboard_rect.h))
        v_rect = ctx.artboard_visible_rect
        ctx.artboard[:] = resized_buffer[v_rect.y0:v_rect.y1, v_rect.x0:v_rect.x1]

    def _update_size(self) -> None:
        # Setting the artboard size will dirty the canvas.
        self.size = self._preview.buffer.shape[1::-1]
