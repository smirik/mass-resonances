from typing import List, Iterable, Tuple, Dict

import numpy as np
import os
from abc import abstractmethod

from resonances.entities.resonance.twobodyresonance import ResonanceMixin

from resonances.entities.body import LONG
from resonances.entities.body import PERI
from .collection import OrbitalElementSet
from .collection import OrbitalElementSetCollection
import pandas as pd
SMALL_BODY = 'small_body'
BIG_BODIES = 'big_bodies'
HEADER_LINE_COUNT = 4


class _AggregatedElements:
    def __init__(self, small_body: OrbitalElementSet,
                 big_bodies: List[OrbitalElementSet]):
        self._big_bodies = big_bodies
        self._small_body = small_body

    @property
    def big_bodies(self) -> List[OrbitalElementSet]:
        return self._big_bodies

    @property
    def small_body(self) -> OrbitalElementSet:
        return self._small_body


class ElementCountException(Exception):
    pass


class PhaseCountException(Exception):
    pass


class IOrbitalElementSetFacade(object):
    """
    General class that gives interface for representation set of orbital elements.
    """

    def __init__(self, orbital_element_sets: List[OrbitalElementSetCollection]):
        """
        :param orbital_element_sets: object
        :return:
        """
        self._orbital_element_sets = orbital_element_sets
        if len(self._orbital_element_sets) == 1:
            return
        for i in range(1, len(orbital_element_sets)):
            first_elems_len = len(orbital_element_sets[i - 1])
            second_elems_len = len(orbital_element_sets[i])
            if not (first_elems_len == second_elems_len):
                raise ElementCountException(
                    'count of first body elements: %i not equal second body: %i' %
                    (first_elems_len, second_elems_len)
                )

    def _make_res_data(self, aei_data: pd.DataFrame, phases: np.ndarray) -> pd.DataFrame:
        res_data_args = [
            aei_data['Time (years)'],
            phases,
            aei_data['a'].values,
            aei_data['e'].values,
            np.radians(aei_data['i'].values.astype(int)),
            np.radians(aei_data['node'].values.astype(int)),
            np.radians(aei_data['long'].values),
        ]

        for planet in self._orbital_element_sets:
            res_data_args.append(planet.orbital_elements['a'].values)
            res_data_args.append(planet.orbital_elements['e'].values)

        res_data = np.column_stack(res_data_args)
        res_data = pd.DataFrame(res_data)

        return res_data

    def _get_body_orbital_elements(self, aei_data: List[str]) \
            -> Iterable[_AggregatedElements]:
        """Build orbital elements of bodies from data of the .aei file.
        :return: generator of dictionaries, contains set of orbital elements
        for two planets and asteroid.
        """
        for i, line in enumerate(aei_data):
            if i < HEADER_LINE_COUNT:
                continue

            index = i - HEADER_LINE_COUNT
            var = [x[index] for x in self._orbital_element_sets]
            yield _AggregatedElements(OrbitalElementSet(line), var)

    def write_to_resfile(self, res_filepath: str, aei_data: pd.DataFrame):
        """Saves data, returned by method get_elements to res file.
        :param aei_data:
        :param res_filepath: path of file for saving
        instances of internal class, that represents set of orbital elemetns
        in res file format.
        """
        if not os.path.exists(os.path.dirname(res_filepath)):
            os.makedirs(os.path.dirname(res_filepath))
        res_data = self.get_elements(aei_data)
        res_data.to_csv(res_filepath, sep=' ', header=False, index=False)

    @abstractmethod
    def get_elements(self, aei_data: pd.DataFrame) -> pd.DataFrame:
        pass


class ComputedOrbitalElementSetFacade(IOrbitalElementSetFacade):
    """Facade of set of the orbital elements, that doesn't compute resonant
    phase. It represents elements by pointed sets of orbital elements of the
    planets and resonant phases.
    """

    def __init__(self, orbital_element_sets: List[OrbitalElementSetCollection],
                 resonant_phases: List[float]):
        """
        :param orbital_element_sets:
        :param resonant_phases:
        :return:
        """
        super(ComputedOrbitalElementSetFacade, self).__init__(orbital_element_sets)
        second_elems_len = len(orbital_element_sets[0])
        if not (len(resonant_phases) == second_elems_len):
            raise PhaseCountException(
                'Number of resonant phases %i is not equal %i' %
                (len(resonant_phases), second_elems_len)
            )
        self._resonant_phases = resonant_phases

    def get_elements(self, aei_data: pd.DataFrame) -> pd.DataFrame:
        """
        :param aei_data:
        :return:
        """
        phases = np.array(self._resonant_phases)
        res_data = self._make_res_data(aei_data, phases)
        return res_data


class AsteroidElementCountException(Exception):
    pass


def _get_longitutes(aei_data: pd.DataFrame):
    times = aei_data['Time (years)']
    p_longs = np.radians(aei_data['long'])
    mean_anomalies = np.radians(aei_data['M'])
    m_longs = p_longs + mean_anomalies
    return m_longs, p_longs, times


class ResonanceOrbitalElementSetFacade(IOrbitalElementSetFacade):
    """Facade of set of the orbital elements, that computes resonant phase for
    pointed resonance. It represents elements by pointed sets of orbital
    elements of the planets and computed resonant phases.
    """

    def __init__(self, orbital_element_sets: List[OrbitalElementSetCollection],
                 resonance: ResonanceMixin):
        """
        :param orbital_element_sets:
        :param resonance:
        :return:
        """
        super(ResonanceOrbitalElementSetFacade, self).__init__(orbital_element_sets)
        self._resonance = resonance

    def _validate_asteroid_orbital_elements(self, from_aei_data: pd.DataFrame):
        planets_elements_count = len(self._orbital_element_sets[0])
        asteroid_elements_count = from_aei_data.shape[0]
        if planets_elements_count != asteroid_elements_count:
            raise AsteroidElementCountException(
                'Number of elements (%i) for asteroid in aei file is not '
                'equal to number of elements (%i) for planets.' %
                (planets_elements_count, asteroid_elements_count))

    def get_resonant_phases(self, aei_data: pd.DataFrame) -> Iterable[Tuple[float, float]]:
        self._validate_asteroid_orbital_elements(aei_data)
        phases = np.zeros(aei_data.shape[0])
        for big_body, set_ in zip(self._resonance.get_big_bodies(), self._orbital_element_sets):
            m_longs, p_longs, times = _get_longitutes(set_.orbital_elements)
            summand1 = m_longs * big_body.longitude_coeff
            summand2 = p_longs * big_body.perihelion_longitude_coeff
            phases += summand1 + summand2

        m_longs, p_longs, times = _get_longitutes(aei_data)
        small_body = self._resonance.small_body
        phases += (
            m_longs * small_body.longitude_coeff +
            p_longs * small_body.perihelion_longitude_coeff
        )

        phases = np.mod(phases, 2 * np.pi)
        mask = np.where(phases > np.pi)
        phases[mask] -= 2 * np.pi

        return [(x, y) for x, y in zip(times, phases)]

    def get_elements(self, aei_data: pd.DataFrame) -> pd.DataFrame:
        """
        :param aei_data:
        :return:
        """
        time_phases = self.get_resonant_phases(aei_data)
        phases = np.array(time_phases)[:, 1]
        res_data = self._make_res_data(aei_data, phases)
        return res_data


def _get_longitudes(from_elem_sets: List[OrbitalElementSet]) -> List[Dict[str, float]]:
    res = []
    for elems in from_elem_sets:
        res.append({
            LONG: elems.m_longitude,
            PERI: elems.p_longitude
        })
    return res
