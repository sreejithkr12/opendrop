from itertools import chain
from typing import List, Tuple

from gi.repository import Gtk
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.lines import Line2D

from opendrop.gtk_specific.GtkWidgetView import GtkWidgetView
from opendrop.gtk_specific.GtkWindowView import GtkWindowView


def pretty_time(seconds: float) -> str:
    seconds = round(seconds)

    s = seconds % 60
    seconds //= 60
    m = seconds % 60
    seconds //= 60
    h = seconds

    return '{h:0>2}:{m:0>2}:{s:0>2}'.format(h=h, m=m, s=s)


class DropSnapshotListStoreUpdater:
    def __init__(self, list_store: Gtk.ListStore, tree_iter: Gtk.TreeIter):
        self._list_store = list_store  # type: Gtk.ListStore
        self._tree_iter = tree_iter  # type: Gtk.TreeIter

    def set_frame_num(self, value: int) -> None:
        self._list_store.set(self._tree_iter, 0, value)

    def set_status(self, value: str) -> None:
        self._list_store.set(self._tree_iter, 1, value)


class IFTResultsView(GtkWindowView):
    TITLE = 'Results'

    def setup(self):
        body = Gtk.Grid()
        self.window.add(body)

        self.window.set_default_size(800, 600)

        # Progress
        progress_container = Gtk.Grid(row_spacing=5, column_spacing=5, margin=5)
        progress_container.props.margin_top = 10
        progress_container.props.margin_left = 20
        progress_container.props.margin_right = 20
        body.attach(progress_container, 0, 0, 1, 1)

        self.progress_bar = Gtk.ProgressBar(show_text=True, hexpand=True)
        progress_container.attach(self.progress_bar, 0, 0, 5, 1)

        time_elapsed_contaier = Gtk.Grid(column_spacing=5)
        progress_container.attach(time_elapsed_contaier, 0, 1, 1, 1)

        time_elapsed_lbl = Gtk.Label('Time elapsed:', halign=Gtk.Align.START)
        time_elapsed_contaier.attach(time_elapsed_lbl, 0, 1, 1, 1)

        self.time_elapsed_text = Gtk.Label('00:00:00', halign=Gtk.Align.START)
        time_elapsed_contaier.attach(self.time_elapsed_text, 1, 1, 1, 1)

        progress_container.attach(Gtk.Grid(hexpand=True), 1, 1, 1, 1)

        self.time_remaining_container = Gtk.Grid(column_spacing=5)
        progress_container.attach(self.time_remaining_container, 2, 1, 1, 1)

        time_remaining_lbl = Gtk.Label('Remaining:', halign=Gtk.Align.START)
        self.time_remaining_container.attach(time_remaining_lbl, 0, 1, 1, 1)

        self.time_remaining_text = Gtk.Label('?', halign=Gtk.Align.START)
        self.time_remaining_container.attach(self.time_remaining_text, 1, 1, 1, 1)

        # Content
        content_container = Gtk.Grid(column_spacing=5, row_spacing=5, margin=5)
        body.attach(content_container, 0, 1, 1, 1)

        content_switcher_container = Gtk.Grid(column_spacing=5)
        content_container.attach(content_switcher_container, 0, 0, 1, 1)

        sep_outer = Gtk.Grid(vexpand=False)
        content_switcher_container.attach(sep_outer, 0, 0, 1, 1)
        sep = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        sep.props.hexpand = True
        sep.props.valign = Gtk.Align.CENTER
        sep_outer.attach(Gtk.Grid(vexpand=True), 0, 0, 1, 1)
        sep_outer.attach(sep, 0, 1, 1, 1)
        sep_outer.attach(Gtk.Grid(vexpand=True), 0, 2, 1, 1)

        sep_outer = Gtk.Grid(vexpand=False)
        content_switcher_container.attach(sep_outer, 2, 0, 1, 1)
        sep = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        sep.props.hexpand = True
        sep.props.valign = Gtk.Align.CENTER
        sep_outer.attach(Gtk.Grid(vexpand=True), 0, 0, 1, 1)
        sep_outer.attach(sep, 0, 1, 1, 1)
        sep_outer.attach(Gtk.Grid(vexpand=True), 0, 2, 1, 1)

        main_stack_switcher = Gtk.StackSwitcher()
        content_switcher_container.attach(main_stack_switcher, 1, 0, 1, 1)

        main_stack = Gtk.Stack()
        content_container.attach(main_stack, 0, 1, 1, 1)
        main_stack_switcher.props.stack = main_stack

        drop_snapshots_view_container = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        main_stack.add_titled(drop_snapshots_view_container, 'experiment_notebook', 'Results')

        self.drop_snapshots_list_store = Gtk.ListStore(int, str)

        drop_snapshots_tree_view_sw = Gtk.ScrolledWindow(min_content_width=150)
        drop_snapshots_view_container.attach(drop_snapshots_tree_view_sw, 0, 0, 1, 1)

        self.drop_snapshots_tree_view = Gtk.TreeView.new_with_model(self.drop_snapshots_list_store)
        self.drop_snapshots_tree_view.props.vexpand = True
        self.drop_snapshots_tree_view.props.activate_on_single_click = True
        drop_snapshots_tree_view_sw.add(self.drop_snapshots_tree_view)

        self.drop_snapshots_tree_view.connect(
            'cursor-changed',
            lambda w: self.drop_snapshot_view_stack.set_visible_child_name(w.get_cursor()[0].to_string())
        )

        # Tree view columns
        drop_snapshots_tree_view_frame_column = Gtk.TreeViewColumn(title='Frame', cell_renderer=Gtk.CellRendererText(),
                                                                   text=0)
        drop_snapshots_tree_view_frame_column.props.fixed_width = 50
        self.drop_snapshots_tree_view.append_column(drop_snapshots_tree_view_frame_column)

        drop_snapshots_tree_view_status_column = Gtk.TreeViewColumn(title='Status',
                                                                    cell_renderer=Gtk.CellRendererText(), text=1)
        drop_snapshots_tree_view_status_column.props.fixed_width = 100
        self.drop_snapshots_tree_view.append_column(drop_snapshots_tree_view_status_column)

        drop_snapshots_view_container.attach(Gtk.Separator.new(Gtk.Orientation.VERTICAL), 1, 0, 1, 1)

        # Drop snapshot preview
        self.drop_snapshot_view_stack = Gtk.Stack()
        drop_snapshots_view_container.attach(self.drop_snapshot_view_stack, 2, 0, 1, 1)

        graphs_container = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
        main_stack.add_titled(graphs_container, 'graphs', 'Graphs')

        graphs_figure = Figure()
        graphs_figure.subplots_adjust(hspace=0)
        self.graphs_canvas = FigureCanvas(graphs_figure)
        self.graphs_canvas.props.hexpand = True
        self.graphs_canvas.props.vexpand = True
        graphs_container.attach(self.graphs_canvas, 0, 0, 1, 1)

        self.ift_axes = graphs_figure.add_subplot(3, 1, 1)
        self.ift_axes.set_ylabel('IFT (mN/m)')
        self.vol_axes = graphs_figure.add_subplot(3, 1, 2, sharex=self.ift_axes)
        self.vol_axes.xaxis.set_ticks_position('both')
        self.vol_axes.set_ylabel('Vol. (mm³)')
        self.sur_axes = graphs_figure.add_subplot(3, 1, 3, sharex=self.ift_axes)
        self.sur_axes.xaxis.set_ticks_position('both')
        self.sur_axes.set_ylabel('Sur. (mm²)')

        for lbl in chain(self.ift_axes.get_xticklabels(), self.vol_axes.get_xticklabels()):
            lbl.set_visible(False)

        self.ift_line = self.ift_axes.plot([], [], marker='o', color='red')[0]  # type: Line2D
        self.vol_line = self.vol_axes.plot([], [], marker='o', color='blue')[0]  # type: Line2D
        self.sur_line = self.sur_axes.plot([], [], marker='o', color='green')[0]  # type: Line2D

        # Footer
        footer_container = Gtk.Grid(column_spacing=5, hexpand=True)
        footer_container.get_style_context().add_class('gray-box')

        footer_container_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        footer_container_css.load_from_data(bytes('''
            .gray-box {
                background-color: gainsboro;
                padding: 5px;
            }
        ''', encoding='utf-8'))

        footer_container.get_style_context().add_provider(footer_container_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        body.attach(footer_container, 0, 2, 1, 1)

        back_btn = Gtk.Button.new_from_icon_name('go-previous', Gtk.IconSize.BUTTON)
        footer_container.attach(back_btn, 0, 0, 1, 1)
        back_btn.connect('clicked', lambda w: self.events.on_back_btn_clicked.fire())

        save_btn = Gtk.Button.new_from_icon_name('media-floppy', Gtk.IconSize.BUTTON)
        footer_container.attach(save_btn, 1, 0, 1, 1)
        save_btn.connect('clicked', lambda w: self.events.on_save_btn_clicked.fire())


        self.window.show_all()

    def add_drop_snapshot(self, drop_snapshot_preview_view: GtkWidgetView):
        path = str(len(self.drop_snapshots_list_store))
        tree_iter = self.drop_snapshots_list_store.append(row=(-1, ''))

        drop_snapshot_preview_view.container.show_all()
        self.drop_snapshot_view_stack.add_named(drop_snapshot_preview_view.container, path)

        if self.drop_snapshots_tree_view.get_cursor().path is None:
            self.drop_snapshots_tree_view.set_cursor(path)

        return DropSnapshotListStoreUpdater(self.drop_snapshots_list_store, tree_iter)

    def set_progress(self, value: float) -> None:
        self.progress_bar.props.fraction = value

        if value == 1:
            self.time_remaining_container.hide()
        else:
            self.time_remaining_container.show()

    def set_time_elapsed(self, value: float) -> None:
        self.time_elapsed_text.props.label = pretty_time(value)

    def set_time_remaining(self, value: float) -> None:
        if value == 0:
            self.time_remaining_text.props.label = '?'
            return

        self.time_remaining_text.props.label = pretty_time(value)

    def set_ift_data(self, t: List, v: List) -> None:
        self.ift_line.set_xdata(t)
        self.ift_line.set_ydata(v)
        self.graphs_canvas.draw()

    def set_ift_lims(self, tlim: Tuple[float, float], vlim: Tuple[float, float]):
        self.ift_axes.set_xlim(tlim)
        self.ift_axes.set_ylim(vlim)
        self.graphs_canvas.draw()

    def set_vol_data(self, t: List, v: List) -> None:
        self.vol_line.set_xdata(t)
        self.vol_line.set_ydata(v)
        self.graphs_canvas.draw()

    def set_vol_lims(self, tlim: Tuple[float, float], vlim: Tuple[float, float]):
        self.vol_axes.set_ylim(vlim)
        self.graphs_canvas.draw()

    def set_sur_data(self, t: List, v: List) -> None:
        self.sur_line.set_xdata(t)
        self.sur_line.set_ydata(v)
        self.graphs_canvas.draw()

    def set_sur_lims(self, tlim: Tuple[float, float], vlim: Tuple[float, float]):
        self.sur_axes.set_ylim(vlim)
        self.graphs_canvas.draw()
