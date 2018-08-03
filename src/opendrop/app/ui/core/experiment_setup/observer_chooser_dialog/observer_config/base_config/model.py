from abc import abstractmethod
from typing import MutableMapping, Any, Optional

from opendrop.mvp.Model import Model
from opendrop.observer.bases import ObserverType


class ObserverConfigRequest(Model):
    @property
    @abstractmethod
    def type(self) -> Optional[ObserverType]: pass

    @property
    @abstractmethod
    def opts(self) -> MutableMapping[str, Any]: pass
