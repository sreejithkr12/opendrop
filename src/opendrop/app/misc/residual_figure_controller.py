from matplotlib.figure import Figure


class ResidualFigureController:
    def __init__(self, figure: Figure):
        self.figure = figure

        self._sdata = None
        self._residuals = None

    def redraw(self):
        self.figure.clear()

        if self.sdata is None or self.residuals is None:
            return

        axes = self.figure.add_subplot(1, 1, 1)
        axes.plot(self.sdata, self.residuals, color='#0080ff', marker='o', linestyle='')

        if self.figure.canvas:
            self.figure.canvas.draw()

    @property
    def sdata(self):
        return self._sdata

    @sdata.setter
    def sdata(self, value):
        self._sdata = value
        self.redraw()

    @property
    def residuals(self):
        return self._residuals

    @residuals.setter
    def residuals(self, value):
        self._residuals = value
        self.redraw()
