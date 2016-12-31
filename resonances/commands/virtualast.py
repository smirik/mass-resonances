import logging
from resonances.shortcuts import FAIL, ENDC
from numpy.random import normal as normal_dist
from typing import Tuple
from typing import Iterable
from typing import List
from resonances.catalog import asteroid_gen
from resonances.catalog import read_header


from .variations import grab_variations
from .variations import VARIATION_NAME_RESOLVE_MAP
from .variations import VariationsData


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


class VirtualAsteroidCatalogBuilder:
    def __init__(self, catalog: str, start: int = None, stop: int = None):
        self._catalog = catalog
        self._start = start
        self._stop = stop
        self._header_lines = [x for x in read_header(catalog)]

    def _gen_distributions(self) -> Iterable[List[_DistributionParams]]:
        for name, orbital_elems in asteroid_gen(self._catalog, self._start, self._stop):
            names, variations_matrix = grab_variations(iter([name]))
            asteroid_variations = variations_matrix[0]
            builder = _DistributionParamsBuilder(names, asteroid_variations)

            axis_dist = builder.build(orbital_elems[1], 'a')
            ecc_dist = builder.build(orbital_elems[2], 'e')
            inc_dist = builder.build(orbital_elems[3], 'i')
            arg_peric_dist = builder.build(orbital_elems[4], 'arg. peric.')
            long_node_dist = builder.build(orbital_elems[5], 'long. node')
            mean_anomaly_dist = builder.build(orbital_elems[6], 'mean anomaly')
            dists = [axis_dist, ecc_dist, inc_dist, long_node_dist,
                     arg_peric_dist, mean_anomaly_dist]
            yield name, dists

    def build(self, count: int):
        if count is None or count < 1:
            logging.error('%sCount of virtual asteroids for generating must be more than 1%s',
                          FAIL, ENDC)
            exit(-1)
        for item in self._header_lines:
            print(item)

        for name, dists in self._gen_distributions():
            for i, virtual_orbital_elems in enumerate(_virtual_asteroid_gen(dists, count)):
                arr = virtual_orbital_elems
                arr[5], arr[4] = arr[4], arr[5]
                virtual_orbital_elems_str = '\t'.join(['%.16E' % x for x in virtual_orbital_elems])
                print("'%s.%i'" % (name, i), virtual_orbital_elems_str, 0, 0, 0, sep='\t')


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
