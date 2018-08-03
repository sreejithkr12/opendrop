import json
from pathlib import Path
from typing import Union, Iterator, Any

from collections.abc import MutableMapping, Mapping, MutableSequence, Sequence


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, PersistentDataDict):
            d = dict(o)
        elif isinstance(o, PersistentDataList):
            d = list(o)
        else:
            d = super().default(o)

        return d


def json_serializable(x):
    try:
        json.dumps(x, cls=CustomJSONEncoder)
        return True
    except TypeError:
        return False


class PersistentDataContainer:
    def __init__(self, master: 'PersistentDataMaster'):
        self.master = master

    def _changed(self) -> None:
        self.master.save()

    def _convert(self, v) -> Any:
        if isinstance(v, Mapping):
            v = PersistentDataDict(self.master, v)
        elif isinstance(v, Sequence) and not isinstance(v, str):
            v = PersistentDataList(self.master, v)
        elif not json_serializable(v):
            raise TypeError('{!r} is not JSON serializable'.format(v))

        return v


class PersistentDataList(PersistentDataContainer, MutableSequence):
    def __init__(self, master: 'PersistentDataMaster', base_data: Sequence):
        assert json_serializable(base_data)
        super().__init__(master)

        self.data = []

        for v in base_data:
            self.append(v)

    def insert(self, index, value) -> None:
        value = self._convert(value)
        self.data.insert(index, value)
        self._changed()

    def __getitem__(self, index) -> Any:
        return self.data.__getitem__(index)

    def __setitem__(self, index, value) -> None:
        value = self._convert(value)
        self.data.__setitem__(index, value)
        self._changed()

    def __delitem__(self, index) -> None:
        self.data.__delitem__(index)
        self._changed()

    def __len__(self) -> int:
        return self.data.__len__()

    def __eq__(self, other):
        return self.data == other

    def __str__(self) -> str:
        return str(self.data)

    def __repr__(self) -> str:
        return '{classname}({root!r}, {data!r})'.format(classname=PersistentDataList.__name__, root=self.master,
                                                        data=self.data)


class PersistentDataDict(PersistentDataContainer, MutableMapping):
    def __init__(self, master: 'PersistentDataMaster', base_data: Mapping):
        assert json_serializable(base_data)
        super().__init__(master)

        self.data = {}

        for k, v in base_data.items():
            self.__setitem__(k, v)

    def __getitem__(self, k) -> Any:
        return self.data.__getitem__(k)

    def __setitem__(self, k, v) -> None:
        v = self._convert(v)
        self.data.__setitem__(k, v)
        self._changed()

    def __delitem__(self, v) -> None:
        self.data.__delitem__(v)

        self._changed()

    def __iter__(self) -> Iterator:
        return self.data.__iter__()

    def __len__(self) -> int:
        return self.data.__len__()

    def __str__(self) -> str:
        return str(self.data)

    def __repr__(self) -> str:
        return '{classname}({root!r}, {data!r})'.format(classname=PersistentDataDict.__name__, root=self.master,
                                                        data=self.data)


class PersistentDataMaster:
    data = None

    def __init__(self, fp: Union[str, Path]):
        self.fp = Path(fp)  # type: Path

    def save(self) -> None:
        with self.fp.open('w') as f:
            json.dump(self.data, f, indent=2, cls=CustomJSONEncoder)

    def __repr__(self) -> str:
        return '{classname}({fp!r})'.format(classname=type(self).__name__, fp=str(self.fp))


class PersistentDataMasterDict(PersistentDataMaster, PersistentDataDict):
    def __init__(self, fp: Union[str, Path]):
        PersistentDataMaster.__init__(self, fp)

        with self.fp.open() as f:
            data = json.load(f)

        PersistentDataDict.__init__(self, master=self, base_data=data)


class PersistentDataMasterList(PersistentDataMaster, PersistentDataList):
    def __init__(self, fp: Union[str, Path]):
        PersistentDataMaster.__init__(self, fp)

        with self.fp.open() as f:
            data = json.load(f)

        PersistentDataList.__init__(self, master=self, base_data=data)


def open(fp: Union[str, Path]) -> PersistentDataMaster:
    # Need to first open the file to see if it is a list or dict
    with Path(fp).open() as f:
        o = json.load(f)

    if isinstance(o, dict):
        return PersistentDataMasterDict(fp)
    elif isinstance(o, list):
        return PersistentDataMasterList(fp)
    else:
        raise ValueError('Expected `list` or `dict`, got `{}` from file \'{}\'.'.format(type(o).__name__, str(fp)))
