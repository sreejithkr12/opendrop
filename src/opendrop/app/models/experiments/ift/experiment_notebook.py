import asyncio
import csv
import itertools
import shutil
from pathlib import Path
from typing import List, Optional, Mapping, Any, IO, Tuple, Union

import cv2
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from opendrop.app.settings import settings
from opendrop.app.misc.drop_fit_figure_controller import DropFitFigureController
from opendrop.app.misc.residual_figure_controller import ResidualFigureController
from opendrop.image_filter.crop import Crop
from opendrop.mvp.Model import Model
from opendrop.utility import data_binding

from .drop_snapshot import DropSnapshot
from .young_laplace.young_laplace_fit import DoneFlag


def make_unique_filename(directory: Union[Path, str], base_filename: str) -> str:
    directory = Path(directory)
    filename = base_filename

    for i in itertools.count(start=2):
        if not (directory/filename).exists():
            break

        filename = '{base_filename} ({i})'.format(base_filename=base_filename, i=i)

    return filename


class ExperimentSaveRequest(Model):
    def __init__(self, ift_results: 'ExperimentNotebook'):
        super().__init__()

        self._ift_results = ift_results  # type: ExperimentNotebook

        self._save_parent_dir = settings.default_drop_save_parent_directory  # type: Optional[str]
        self._save_name = make_unique_filename(self.save_parent_dir, 'Untitled Drop')
        self._graph_dpi = 300.0  # type: Optional[float]

    @data_binding.property
    def save_parent_dir(self) -> Optional[str]:
        return self._save_parent_dir

    @save_parent_dir.setter
    def save_parent_dir(self, value: Optional[str]) -> None:
        self._save_parent_dir = value

    @data_binding.property
    def save_name(self) -> Optional[str]:
        return self._save_name

    @save_name.setter
    def save_name(self, value: Optional[str]) -> None:
        self._save_name = value

    @property
    def save_dir(self) -> Path:
        return Path(self.save_parent_dir)/self.save_name

    @data_binding.property
    def graph_dpi(self) -> Optional[float]:
        return self._graph_dpi

    @graph_dpi.setter
    def graph_dpi(self, value: Optional[float]) -> None:
        self._graph_dpi = value

    def validate(self) -> Mapping[str, Any]:
        errors = {}

        if self.graph_dpi is None or self.graph_dpi <= 0:
            errors['graph_dpi'] = 'Graph DPI must be a positive number'

        if self.save_dir is None:
            errors['save_dir'] = 'Save directory can\'t be empty'

        return errors

    def submit(self) -> None:
        assert not self.validate()

        settings.default_drop_save_parent_directory = self.save_parent_dir

        self._ift_results.save(self)


def _save_drop_properties(drop: DropSnapshot, f: IO):
    writer = csv.writer(f)

    writer.writerow(
        ['Timestamp (s)', 'IFT (mN/m)', 'Volume (mm^3)', 'Surface Area (mm^2)', 'Worthington', 'Bond',
         'Apex Radius (mm)', 'Apex X (px)', 'Apex Y (px)', 'Drop Region (px)', 'Needle Width (mm)',
         'Scale (mm/px)', 'Inner density (kg/mm^3)', 'Outer Density (kg/mm^3)', 'Gravity (m/s^2)']
    )

    drop_region_px = (np.array(drop.drop_region) * drop.image.shape[1::-1]).astype(int)
    drop_region_px_str = '[[{0[0][0]}, {0[0][1]}], [{0[1][0]}, {0[1][1]}]]'.format(drop_region_px)

    writer.writerow(
        [drop.timestamp, drop.derived.ift, drop.derived.volume, drop.derived.surface_area, drop.derived.worthington,
         drop.bond, drop.apex_radius, drop.apex_x, drop.apex_y, drop_region_px_str, drop.needle_width, drop.scale,
         drop.inner_density, drop.outer_density, drop.gravity]
    )


def _save_drop_image(drop: DropSnapshot, fp: Path) -> None:
    if not drop.observation.volatile:
        return

    img = drop.observation.image
    img = cv2.cvtColor(img, code=cv2.COLOR_RGB2BGR)

    cv2.imwrite(str(fp), img)


def _save_drop_fit_figure(drop: DropSnapshot, fp: Path, dpi: float) -> None:
    figure = Figure(dpi=dpi)
    controller = DropFitFigureController(figure)

    controller.drop_image = Crop(drop.drop_region).apply(drop.observation.image)
    controller.drop_image_scale = drop.scale
    controller.drop_contour_fitted = drop.drop_contour_fitted
    controller.drop_contour = drop.drop_contour

    FigureCanvasAgg(figure).print_figure(str(fp), dpi=dpi)


def _save_drop_residuals_figure(drop: DropSnapshot, fp: Path, dpi: float) -> None:
    figure = Figure(dpi=dpi)
    controller = ResidualFigureController(figure)

    controller.sdata = drop.residuals[:, 0]
    controller.residuals = drop.residuals[:, 1]

    FigureCanvasAgg(figure).print_figure(str(fp), dpi=dpi)


def _save_drop_contours(drop: DropSnapshot, raw_f: IO, fitted_f: IO) -> None:
    writer = csv.writer(raw_f)
    writer.writerows(drop.drop_contour)

    writer = csv.writer(fitted_f)
    writer.writerows(drop.drop_contour_fitted)


def _save_drop_residuals(drop: DropSnapshot, f: IO) -> None:
    writer = csv.writer(f)
    writer.writerows(drop.residuals)


def _padded_lim(data: List, pad_percent: float = 0.1) -> Tuple[float, float]:
    pad = (max(data) - min(data)) * pad_percent
    pad = min(min(map(abs, data)), pad)

    return min(data) - pad, max(data) + pad


def _save_drops_graphs(drops: List[DropSnapshot], dir_: Path, dpi: float) -> None:
    t = []
    v_ift = []
    v_vol = []
    v_sur = []

    for drop in drops:
        if not drop.done or not (drop.fit.flags & DoneFlag.CONVERGED == DoneFlag.CONVERGED):
            continue

        t.append(drop.observation.timestamp)
        v_ift.append(drop.derived.ift)
        v_vol.append(drop.derived.volume)
        v_sur.append(drop.derived.surface_area)

    if len(t) <= 1:
        # No need to save graphs for just one drop
        return

    t_lim = min(t), max(t)

    figure_ift = Figure()
    axes_ift = figure_ift.add_subplot(1, 1, 1)
    axes_ift.plot(t, v_ift, color='red')
    axes_ift.set_xlabel('Time (s)')
    axes_ift.set_ylabel('IFT (mN/m)')
    axes_ift.set_xlim(t_lim)
    axes_ift.set_ylim(_padded_lim(v_ift))

    figure_vol = Figure()
    axes_vol = figure_vol.add_subplot(1, 1, 1)
    axes_vol.plot(t, v_vol, color='blue')
    axes_vol.set_xlabel('Time (s)')
    axes_vol.set_ylabel('Volume (mm³)')
    axes_vol.set_xlim(t_lim)
    axes_vol.set_ylim(_padded_lim(v_vol))

    figure_sur = Figure()
    axes_sur = figure_sur.add_subplot(1, 1, 1)
    axes_sur.plot(t, v_sur, color='green')
    axes_sur.set_xlabel('Time (s)')
    axes_sur.set_ylabel('Surface Area (mm²)')
    axes_sur.set_xlim(t_lim)
    axes_sur.set_ylim(_padded_lim(v_sur))

    FigureCanvasAgg(figure_ift).print_figure(str(dir_/'ift.png'), dpi)
    FigureCanvasAgg(figure_vol).print_figure(str(dir_/'volume.png'), dpi)
    FigureCanvasAgg(figure_sur).print_figure(str(dir_/'surface_area.png'), dpi)


def _save_drops_timeline(drops: List[DropSnapshot], f: IO):
    headers = ['Timestamp (s)',
               'IFT (mN/m)',
               'Volume (mm^3)',
               'Surface Area (mm^2)',
               'Worthington',
               'Bond',
               'Apex Radius (mm)']  # type: List[str]

    data = [[drop.timestamp, drop.derived.ift, drop.derived.volume, drop.derived.surface_area, drop.derived.worthington,
             drop.bond, drop.apex_radius] for drop in drops if drop.status == 'Done']  # type: List[List]

    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(data)


def save_drops(ift_results: 'ExperimentNotebook', save_request: ExperimentSaveRequest) -> None:
    save_dir = save_request.save_dir  # type: Path

    try:
        shutil.rmtree(str(save_dir))
    except FileNotFoundError:
        pass
    else:
        save_dir.mkdir(parents=True)

    for i, ds in enumerate(ift_results.drop_snapshots):
        if not ds.done or not (ds.fit.flags & DoneFlag.CONVERGED == DoneFlag.CONVERGED):
            continue

        drop_dir = save_dir/'drops'/str(i)
        drop_dir.mkdir(parents=True, exist_ok=True)

        with (drop_dir/'properties.csv').open(mode='w') as f:
            _save_drop_properties(ds, f)

        _save_drop_image(ds, drop_dir/'capture.png')
        _save_drop_fit_figure(ds, drop_dir/'fit_figure.png', dpi=save_request.graph_dpi)
        _save_drop_residuals_figure(ds, drop_dir/'residuals_figure.png', dpi=save_request.graph_dpi)

        with (drop_dir/'raw_contour.csv').open(mode='w') as raw_f, \
             (drop_dir/'fitted_contour.csv').open(mode='w') as fitted_f:
            _save_drop_contours(ds, raw_f, fitted_f)

        with (drop_dir/'residuals.csv').open(mode='w') as f:
            _save_drop_residuals(ds, f)

    graphs_dir = save_dir/'graphs'
    graphs_dir.mkdir(parents=True, exist_ok=True)

    _save_drops_graphs(ift_results.drop_snapshots, graphs_dir, save_request.graph_dpi)
    _save_drops_timeline(ift_results.drop_snapshots, (save_dir/'timeline.csv').open(mode='w'))


class ExperimentNotebook(Model):
    def __init__(self, drop_snapshots: List[DropSnapshot]):
        super().__init__()

        self.start_time = asyncio.get_event_loop().time()  # type: float
        self._current_time = self.start_time
        self._time_elapsed = self.start_time  # type: float

        self.drop_snapshots = drop_snapshots  # type: List[DropSnapshot]

        for ds in self.drop_snapshots:
            def handle_drop_snapshot_status_changed():
                self.update_progress()

            ds.events.on_status_changed.connect(handle_drop_snapshot_status_changed, strong_ref=True)
            handle_drop_snapshot_status_changed()

        self.current_time_update_loop()

    def create_save_request(self) -> ExperimentSaveRequest:
        return ExperimentSaveRequest(self)

    def save(self, save_request: ExperimentSaveRequest) -> None:
        save_drops(self, save_request)

    def cancel(self) -> None:
        for ds in self.drop_snapshots:
            ds.observation.cancel()

            if ds.fit is not None:
                ds.fit.cancel()

    @property
    def current_time(self) -> float:
        return self._current_time

    @current_time.setter
    def current_time(self, value: float) -> None:
        self._current_time = value

        self.events.on_time_remaining_changed.fire()
        self.events.on_time_elapsed_changed.fire()

    # todo: composite property, triggered by other events
    @property
    def time_remaining(self) -> float:
        time_remaining = max(ds.observation.time_until_ready for ds in self.drop_snapshots)
        return time_remaining

    # todo: composite property, clock object?
    @property
    def time_elapsed(self) -> float:
        return self.current_time - self.start_time

    def current_time_update_loop(self) -> None:
        if self.progress == 1:
            return

        self.current_time = asyncio.get_event_loop().time()

        asyncio.get_event_loop().call_later(delay=1, callback=self.current_time_update_loop)

    # todo: composite property
    @property
    def progress(self) -> float:
        total = len(self.drop_snapshots)
        done = sum(ds.done for ds in self.drop_snapshots)

        return done / total

    def update_progress(self) -> None:
        self.events.on_progress_changed.fire()
