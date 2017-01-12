"""
Module aims to create virtual asteroids.
"""
import logging
from resonances.shortcuts import FAIL, ENDC
from numpy.random import normal as normal_dist
from typing import Tuple
from typing import Iterable
from typing import List
from resonances.catalog import asteroid_gen
from resonances.catalog import read_header
from concurrent.futures import ThreadPoolExecutor
from asyncio.futures import Future

from .variations import grab_variations
from .variations import VARIATION_NAME_RESOLVE_MAP

from resonances.settings import Config

CONFIG = Config.get_params()
THREADS = CONFIG['system']['threads']


_name_dists = []  # type: List[Tuple[str, List[_DistributionParams]]]


class _DistributionParams:
    def __init__(self, value: float, variation: float):
        self._value = value
        self._variation = variation

    @property
    def value(self) -> float:
        return self._value

    @property
    def variation(self) -> float:
        return self._variation


class _DistributionParamsBuilder:
    def __init__(self, variations_names: List[str], asteroid_variations: List[float]):
        self._variations_names = variations_names
        self._asteroid_variations = asteroid_variations

    def build(self, orbital_elem: str, orbital_elem_name: str) -> _DistributionParams:
        variation_name = VARIATION_NAME_RESOLVE_MAP[orbital_elem_name]
        variation_index = self._variations_names.index(variation_name)
        variation = self._asteroid_variations[variation_index]
        return _DistributionParams(orbital_elem, float(variation))


def _make_dists(orbital_elems: List[float], names, asteroid_variations):
    """Creates list of distribution parameters."""
    builder = _DistributionParamsBuilder(names, asteroid_variations)
    axis_dist = builder.build(orbital_elems[1], 'a')
    ecc_dist = builder.build(orbital_elems[2], 'e')
    inc_dist = builder.build(orbital_elems[3], 'i')
    arg_peric_dist = builder.build(orbital_elems[4], 'arg. peric.')
    long_node_dist = builder.build(orbital_elems[5], 'long. node')
    mean_anomaly_dist = builder.build(orbital_elems[6], 'mean anomaly')
    dists = [axis_dist, ecc_dist, inc_dist, long_node_dist,
             arg_peric_dist, mean_anomaly_dist]
    return dists


def _dump_dists(name: str, dists: List[_DistributionParams], count: int):
    """Outputs asteroids are made by normal distribition."""
    for i, virtual_orbital_elems in enumerate(_virtual_asteroid_gen(dists, count)):
        arr = virtual_orbital_elems
        arr[5], arr[4] = arr[4], arr[5]
        virtual_orbital_elems_str = '\t'.join(['%.16E' % x for x in virtual_orbital_elems])
        print("'%s.%i'" % (name, i), virtual_orbital_elems_str, 0, 0, 0, sep='\t')


def _accumulate_distributions(future: Future):
    """
    Saves created distribution parameters to global variable.
    """
    global _name_dists
    task_data = future.result()  # type: _TaskData
    orbital_elems = task_data.orbiral_elems
    names = task_data.names
    variations_matrix = task_data.variations_matrix
    asteroid_variations = variations_matrix[0]
    dists = _make_dists(orbital_elems, names, asteroid_variations)
    _name_dists.append((task_data.name, dists))


class _TaskData:
    def __init__(self, name: str, orbiral_elems: List[float], names: List[str],
                 variations_matrix: List[List[float]]):
        self.name = name
        self.orbiral_elems = orbiral_elems
        self.names = names
        self.variations_matrix = variations_matrix


def _wrapped_grab_variations(name: str, orbital_elems: List[float]) -> _TaskData:
    """Forwards name of nominal asteroid and related orbital elements to callback."""
    names, variations_matrix = grab_variations(iter([name]))
    return _TaskData(name, orbital_elems, names, variations_matrix)


class VirtualAsteroidCatalogBuilder:
    """
    Downloads variations of orbital elements of asteroids from pointed catalog
    and builds "virtual" asteroids with orbital elements are made by normal
    distribution based on orbital elements and variations of them.
    """
    def __init__(self, catalog: str, start: int = None, stop: int = None):
        self._catalog = catalog
        self._start = start
        self._stop = stop
        self._header_lines = [x for x in read_header(catalog)]

    def _gen_distributions(self) -> Iterable[List[_DistributionParams]]:
        with ThreadPoolExecutor(max_workers=4) as executor:
            for name, orbital_elems in asteroid_gen(self._catalog, self._start, self._stop):
                task = executor.submit(_wrapped_grab_variations, name, orbital_elems)
                task.add_done_callback(_accumulate_distributions)

    def build(self, count: int):
        global _name_dists
        if count is None or count < 1:
            logging.error('%sCount of virtual asteroids for generating must be more than 1%s',
                          FAIL, ENDC)
            exit(-1)
        for item in self._header_lines:
            print(item)
        self._gen_distributions()

        for name, dists in _name_dists:
            _dump_dists(name, dists, count)


def _virtual_asteroid_gen(dists: Iterable[_DistributionParams], count: int)\
        -> Iterable[List[float]]:
    """
    Generates values based on normal distribution. Return them has same order as the order of dists.

    :param dists: iterable set contains center and variation for normal distribution.
    :param count: number of sets that will be generated.
    """
    for _ in range(count):
        distribition_values = [normal_dist(x.value, x.variation) for x in dists]
        yield distribition_values
