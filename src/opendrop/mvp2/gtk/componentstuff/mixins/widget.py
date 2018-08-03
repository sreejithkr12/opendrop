from abc import abstractmethod


class GtkWidgetComponentMixin:
    def _m_init(self):
        self.connect('destroy', lambda *_: self._tear_down())

    @abstractmethod
    def _tear_down(self) -> None:
        pass
