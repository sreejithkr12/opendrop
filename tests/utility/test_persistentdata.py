import json
from pathlib import Path

from copy import deepcopy

import itertools

import functools
import pytest
from pytest import raises

from opendrop.utility import persistentdata
from opendrop.utility.persistentdata import PersistentDataMaster


def test_stub(): ...


# kind of a hack
def modification(typ, d=None):
    if d is None:
        wrapper = functools.partial(modification, typ)

        try:
            wrapper(object())
        except Exception as e:
            if isinstance(e, StopIteration):
                raise

        return wrapper

    counter = itertools.count()

    if typ == next(counter):
        d['date'] = 'today'
    elif typ == next(counter):
        d['dairy'] = {'milk': 4, 'butter': 5}
    elif typ == next(counter):
        d['gst_exempt'].append('butter')
    elif typ == next(counter):
        del d['gst_exempt'][0]
    elif typ == next(counter):
        d['excise'] = ['cigarettes', 'alcohol']
    elif typ == next(counter):
        del d['fruits']['banana']
    elif typ == next(counter):
        d['inventory'] = {'in_stock': {'apple': 10, 'banana': 20}, 'out_of_stock': [{'milk': {'since': 123}}],
                          'alias': {'tomato': ['tomayto', 'tomahto']}}
    else:
        raise StopIteration

    return d


modifications = list(map(modification, itertools.count()))


class TestPersistentDataMasterDict:
    def setup(self):
        self.data = {'fruits': {'apple': 1, 'banana': 2}, 'gst': 0.1, 'gst_exempt': ['bread', 'milk']}
        self.tmp_path = Path(__file__).parent/'tmp'

        with self.tmp_path.open('w') as f:
            json.dump(self.data, f)

        self.persistent_data = persistentdata.open(self.tmp_path)

    def test_dict_iter(self):
        for a, b in zip(iter(self.persistent_data), iter(self.data)):
            assert a == b

    def test_dict_len(self):
        assert len(self.persistent_data) == len(self.data)

    def test_restoring(self):
        assert self.persistent_data == self.data

    def test_writing_non_json_serializable(self):
        with raises(TypeError):
            self.persistent_data['anomaly'] = object()

    @pytest.mark.parametrize('make_modification', modifications)
    def test_writing(self, make_modification):
        make_modification(self.persistent_data)
        assert self.persistent_data == make_modification(deepcopy(self.data))

        with self.tmp_path.open() as f:
            assert json.load(f) == make_modification(deepcopy(self.data))

    def teardown(self):
        self.tmp_path.unlink()


class TestPersistentDataMasterList:
    def setup(self):
        self.data = ['apples', 'banana', 'grape']
        self.tmp_path = Path(__file__).parent/'tmp'

        with self.tmp_path.open('w') as f:
            json.dump(self.data, f)

        self.persistent_data = persistentdata.open(self.tmp_path)

    def test_restoring(self):
        assert self.persistent_data == self.data

    def teardown(self):
        self.tmp_path.unlink()
