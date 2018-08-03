from typing import Mapping, Any, List

import numpy as np
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

from opendrop.gtk_specific.GtkWidgetView import GtkWidgetView
from opendrop.utility.events import EventSource
from opendrop.app.misc.drop_fit_figure_controller import DropFitFigureController
from opendrop.app.misc.residual_figure_controller import ResidualFigureController


class NoDataLabel(Gtk.Label):
    def __init__(self, **opts):
        super().__init__(**opts)
        self.set_markup('<span font_desc=\'11.0\' color="#00000080"><b>No data</b></span>')


class DropSnapshotView(GtkWidgetView):
    class_events = EventSource()

    def setup(self):
        body = Gtk.Grid(column_spacing=5, margin=5)
        self.container.add(body)

        # Parameters
        parameters_body_outer = Gtk.Grid()
        body.attach(parameters_body_outer, 0, 0, 1, 1)

        parameters_lbl = Gtk.Label(halign=Gtk.Align.START)
        parameters_lbl.set_markup('<span font_desc=\'12.0\'><b>Parameters</b></span>')
        parameters_body_outer.attach(parameters_lbl, 0, 0, 2, 1)

        parameters_body_values = Gtk.Grid(margin=10)
        parameters_body_values.props.margin_top = 15
        parameters_body_outer.attach(parameters_body_values, 0, 1, 1, 1)

        self.parameters_body_values_stack = Gtk.Stack()
        parameters_body_values.add(self.parameters_body_values_stack)

        self.parameters_body_values_stack.add_named(NoDataLabel(vexpand=True), 'no_data')

        parameters_body_values = Gtk.Grid(row_spacing=15, column_spacing=20)
        self.parameters_body_values_stack.add_named(parameters_body_values, 'data')

        ift_lbl = Gtk.Label('IFT (mN/m):', halign=Gtk.Align.START)
        parameters_body_values.attach(ift_lbl, 0, 0, 1, 1)

        self.ift_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.ift_text, 1, 0, 1, 1)
        volume_lbl = Gtk.Label('Volume (mm³):', halign=Gtk.Align.START)
        parameters_body_values.attach(volume_lbl, 0, 1, 1, 1)

        self.volume_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.volume_text, 1, 1, 1, 1)

        surface_area_lbl = Gtk.Label('Surface Area (mm²):', halign=Gtk.Align.START)
        parameters_body_values.attach(surface_area_lbl, 0, 2, 1, 1)

        self.surface_area_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.surface_area_text, 1, 2, 1, 1)

        parameters_body_values.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 3, 2, 1)

        worthington_lbl = Gtk.Label('Worthington:', halign=Gtk.Align.START)
        parameters_body_values.attach(worthington_lbl, 0, 4, 1, 1)

        self.worthington_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.worthington_text, 1, 4, 1, 1)

        bond_number_lbl = Gtk.Label('Bond Number:', halign=Gtk.Align.START)
        parameters_body_values.attach(bond_number_lbl, 0, 5, 1, 1)

        self.bond_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.bond_text, 1, 5, 1, 1)

        apex_radius_lbl = Gtk.Label('Apex Radius (mm):', halign=Gtk.Align.START)
        parameters_body_values.attach(apex_radius_lbl, 0, 6, 1, 1)

        self.apex_radius_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.apex_radius_text, 1, 6, 1, 1)

        apex_lbl = Gtk.Label('Apex (px):', halign=Gtk.Align.START)
        parameters_body_values.attach(apex_lbl, 0, 7, 1, 1)

        self.apex_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.apex_text, 1, 7, 1, 1)

        image_angle_lbl = Gtk.Label('Image Angle:', halign=Gtk.Align.START)
        parameters_body_values.attach(image_angle_lbl, 0, 8, 1, 1)

        self.image_angle_text = Gtk.Label(halign=Gtk.Align.START)
        parameters_body_values.attach(self.image_angle_text, 1, 8, 1, 1)

        # sep = Gtk.Separator.new(Gtk.Orientation.VERTICAL)
        # sep.props.vexpand = True
        # body.attach(sep, 1, 0, 1, 1)

        # Diagnostics
        diagnostics_body_outer = Gtk.Grid(hexpand=True)
        body.attach(diagnostics_body_outer, 2, 0, 1, 1)

        self.diagnostics_body_inner = Gtk.Notebook(hexpand=True)
        self.diagnostics_body_inner.connect('switch-page', self.handle_diagnostics_body_inner_switch_page)
        diagnostics_body_outer.attach(self.diagnostics_body_inner, 0, 1, 1, 1)

        self.class_events.on_diagnostics_switch_page.connect(self.set_diagnostics_page)

        self.drop_fit_body_stack = Gtk.Stack()
        self.diagnostics_body_inner.append_page(self.drop_fit_body_stack, Gtk.Label('Drop Fit'))

        drop_fit_body_no_data_lbl = NoDataLabel(hexpand=True, vexpand=True)
        self.drop_fit_body_stack.add_named(drop_fit_body_no_data_lbl, 'no_data')

        drop_fit_body = Gtk.Grid()
        drop_fit_figure = Figure(figsize=(5, 4), dpi=100)

        drop_fit_canvas = FigureCanvas(drop_fit_figure)
        drop_fit_canvas.props.hexpand = True
        drop_fit_canvas.props.vexpand = True

        self.drop_fit_figure_controller = DropFitFigureController(figure=drop_fit_figure)

        drop_fit_body.attach(drop_fit_canvas, 0, 0, 1, 1)
        self.drop_fit_body_stack.add_named(drop_fit_body, 'data')

        self.drop_fit_residuals_body_stack = Gtk.Stack()
        self.diagnostics_body_inner.append_page(self.drop_fit_residuals_body_stack, Gtk.Label('Residuals'))

        self.drop_fit_residuals_body_no_data_lbl = NoDataLabel(hexpand=True, vexpand=True)
        self.drop_fit_residuals_body_stack.add_named(self.drop_fit_residuals_body_no_data_lbl, 'no_data')

        drop_fit_residuals_body = Gtk.Grid()
        drop_fit_residuals_figure = Figure(figsize=(5, 4), dpi=100)

        drop_fit_residuals_canvas = FigureCanvas(drop_fit_residuals_figure)
        drop_fit_residuals_canvas.props.hexpand = True
        drop_fit_residuals_canvas.props.vexpand = True

        self.drop_fit_residuals_figure_controller = ResidualFigureController(figure=drop_fit_residuals_figure)

        drop_fit_residuals_body.attach(drop_fit_residuals_canvas, 0, 0, 1, 1)
        self.drop_fit_residuals_body_stack.add_named(drop_fit_residuals_body, 'data')

        log_body = Gtk.Grid()
        self.diagnostics_body_inner.append_page(log_body, Gtk.Label('Log'))

        log_text_sw = Gtk.ScrolledWindow(min_content_height=120)
        log_body.add(log_text_sw)

        self.log_text = Gtk.TextView(monospace=True, editable=False, hexpand=True, vexpand=True, margin=10)
        log_text_sw.add(self.log_text)

        self.log_text.props.parent.get_style_context().add_class('white-box')

        log_text_parent_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        log_text_parent_css.load_from_data(bytes('''
                    .white-box {
                        background-color: white;
                    }
                ''', encoding='utf-8'))
        self.log_text.props.parent.get_style_context().add_provider(log_text_parent_css,
                                                                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def update_params(self, params: Mapping[str, Any]) -> None:
        if self.destroyed:
            return

        self.parameters_body_values_stack.set_visible_child_name('data')

        if 'ift' in params:
            self.ift_text.props.label = '{:.4g}'.format(params['ift'])

        if 'volume' in params:
            self.volume_text.props.label = '{:.4g}'.format(params['volume'])

        if 'surface_area' in params:
            self.surface_area_text.props.label = '{:.4g}'.format(params['surface_area'])

        if 'worthington' in params:
            self.worthington_text.props.label = '{:.4g}'.format(params['worthington'])

        if 'apex' in params:
            self.apex_text.props.label = '({:.4g}, {:.4g})'.format(*params['apex'])

        if 'apex_radius' in params:
            self.apex_radius_text.props.label = '{:.4g}'.format(params['apex_radius'])

        if 'image_angle' in params:
            self.image_angle_text.props.label = '{:.4g}°'.format(params['image_angle'])

        if 'bond' in params:
            self.bond_text.props.label = '{:.4g}'.format(params['bond'])

    def set_drop_image(self, drop_image: np.ndarray) -> None:
        if self.destroyed:
            return

        self.drop_fit_body_stack.set_visible_child_name('data')
        self.drop_fit_figure_controller.drop_image = drop_image

    def set_drop_image_scale(self, drop_image_scale: float) -> None:
        self.drop_fit_figure_controller.drop_image_scale = drop_image_scale

    def set_drop_contour(self, drop_contour: List[np.ndarray]) -> None:
        self.drop_fit_figure_controller.drop_contour = drop_contour

    def set_drop_contour_fitted(self, drop_contour_fitted: List[np.ndarray]) -> None:
        self.drop_fit_figure_controller.drop_contour_fitted = drop_contour_fitted

    def set_fit_residuals(self, residuals: np.ndarray) -> None:
        if self.destroyed:
            return

        self.drop_fit_residuals_body_stack.set_visible_child_name('data')

        self.drop_fit_residuals_figure_controller.sdata = residuals[:, 0]
        self.drop_fit_residuals_figure_controller.residuals = residuals[:, 1]

    def set_log_text(self, value: str) -> None:
        self.log_text.get_buffer().set_text(value)

    def handle_diagnostics_body_inner_switch_page(self, w: Gtk.Notebook, child: Gtk.Widget, page_num: int) -> None:
        if self.destroyed:
            return

        self.class_events.on_diagnostics_switch_page.fire(page_num)

    def set_diagnostics_page(self, page_num: int) -> None:
        self.diagnostics_body_inner.handler_block_by_func(self.handle_diagnostics_body_inner_switch_page)
        self.diagnostics_body_inner.set_current_page(page_num)
        self.diagnostics_body_inner.handler_unblock_by_func(self.handle_diagnostics_body_inner_switch_page)

