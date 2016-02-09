from typing import List, Iterable, Dict, Tuple

import os
from abc import abstractmethod
from .collection import OrbitalElementSetCollection
from .collection import OrbitalElementSet
from entities import PERI
from entities.body import LONG
from entities import ThreeBodyResonance
from utils.shortcuts import cutoff_angle


SMALL_BODY = 'small_body'
FIRST_BODY = 'first_body'
SECOND_BODY = 'second_body'
HEADER_LINE_COUNT = 4


class ElementCountException(Exception):
    pass


class PhaseCountException(Exception):
    pass


class IOrbitalElementSetFacade(object):
    """
    General class that gives interface for representation set of orbital elements.
    """

    def __init__(self, firstbody_elements: OrbitalElementSetCollection,
                 secondbody_elements: OrbitalElementSetCollection):
        """
        :param secondbody_elements: must have same length with firstbody_elements.
        :param firstbody_elements: must have same length with secondbody_elements
        :return:
        """
        first_elems = firstbody_elements.orbital_elements
        second_elems = secondbody_elements.orbital_elements
        if not (len(first_elems) == len(second_elems)):
            raise ElementCountException(
                'count of first body elements: %i not equal second body: %i' %
                (len(first_elems), len(second_elems))
            )
        self._firstbody_elements = firstbody_elements
        self._secondbody_elements = secondbody_elements

    def _get_body_orbital_elements(self, aei_data: List[str]) \
            -> Iterable[Dict[str, OrbitalElementSet]]:
        """Build orbital elements of bodies from data of the .aei file.
        :return: generator of dictionaries, contains set of orbital elements
        for two planets and asteroid.
        """
        for i, line in enumerate(aei_data):
            if i < HEADER_LINE_COUNT:
                continue

            index = i - HEADER_LINE_COUNT
            yield {
                SMALL_BODY: OrbitalElementSet(line),
                FIRST_BODY: self._firstbody_elements.orbital_elements[index],
                SECOND_BODY: self._secondbody_elements.orbital_elements[index]
            }

    def write_to_resfile(self, res_filepath: str, aei_data: List[str]):
        """Saves data, returned by method get_elements to res file.
        :param res_filepath: path of file for saving
        :param aei_data: data of aei file. It will be user for building
        instances of internal class, that represents set of orbital elemetns
        in res file format.
        """
        if not os.path.exists(os.path.dirname(res_filepath)):
            os.makedirs(os.path.dirname(res_filepath))
        with open(res_filepath, 'w') as resonance_file:
            for item in self.get_elements(aei_data):
                resonance_file.write(item)

    @abstractmethod
    def get_elements(self, aei_data: List[str]) -> Iterable[str]:
        pass


class ComputedOrbitalElementSetFacade(IOrbitalElementSetFacade):
    """Facade of set of the orbital elements, that doesn't compute resonant
    phase. It represents elements by pointed sets of orbital elements of the
    planets and resonant phases.
    """
    def __init__(self, firstbody_elements: OrbitalElementSetCollection,
                 secondbody_elements: OrbitalElementSetCollection,
                 resonant_phases: List[float]):
        """
        :param secondbody_elements:
        :param firstbody_elements:
        :param resonant_phases:
        :return:
        """
        super(ComputedOrbitalElementSetFacade, self).__init__(
            firstbody_elements, secondbody_elements)
        second_elems = secondbody_elements.orbital_elements
        if not (len(resonant_phases) == len(second_elems)):
            raise PhaseCountException(
                'Number of resonant phases %i is not equal %i' %
                (len(resonant_phases), len(second_elems))
            )
        self._resonant_phases = resonant_phases

    def get_elements(self, aei_data: List[str]) -> Iterable[str]:
        """
        :param aei_data:
        :return:
        """
        for i, orbital_elements in enumerate(self._get_body_orbital_elements(aei_data)):

            resonant_phase = self._resonant_phases[i]
            resonance_data = "%f %f %s %s %s\n" % (
                orbital_elements[SMALL_BODY].time, resonant_phase,
                orbital_elements[SMALL_BODY].serialize_as_asteroid(),
                orbital_elements[FIRST_BODY].serialize_as_planet(),
                orbital_elements[SECOND_BODY].serialize_as_planet()
            )
            yield resonance_data


class ResonanceOrbitalElementSetFacade(IOrbitalElementSetFacade):
    """Facade of set of the orbital elements, that computes resonant phase for
    pointed resonance. It represents elements by pointed sets of orbital
    elements of the planets and computed resonant phases.
    """
    def __init__(self, firstbody_elements: OrbitalElementSetCollection,
                 secondbody_elements: OrbitalElementSetCollection,
                 resonance: ThreeBodyResonance):
        """
        :param secondbody_elements:
        :param firstbody_elements:
        :param resonance:
        :return:
        """
        super(ResonanceOrbitalElementSetFacade, self).__init__(
            firstbody_elements, secondbody_elements)
        self._resonance = resonance

    def get_resonant_phases(self, aei_data: List[str]) -> Iterable[Tuple[float, float]]:
        for orbital_elements in self._get_body_orbital_elements(aei_data):
            resonant_phase = self._resonance.compute_resonant_phase(
                {LONG: orbital_elements[FIRST_BODY].m_longitude,
                 PERI: orbital_elements[FIRST_BODY].p_longitude},
                {LONG: orbital_elements[SECOND_BODY].m_longitude,
                 PERI: orbital_elements[SECOND_BODY].p_longitude},
                {LONG: orbital_elements[SMALL_BODY].m_longitude,
                 PERI: orbital_elements[SMALL_BODY].p_longitude}
            )
            yield orbital_elements[SMALL_BODY].time, cutoff_angle(resonant_phase)

    def get_elements(self, aei_data: List[str]) -> Iterable[str]:
        """
        :param aei_data:
        :return:
        """
        for orbital_elements in self._get_body_orbital_elements(aei_data):
            resonant_phase = self._resonance.compute_resonant_phase(
                {LONG: orbital_elements[FIRST_BODY].m_longitude,
                 PERI: orbital_elements[FIRST_BODY].p_longitude},
                {LONG: orbital_elements[SECOND_BODY].m_longitude,
                 PERI: orbital_elements[SECOND_BODY].p_longitude},
                {LONG: orbital_elements[SMALL_BODY].m_longitude,
                 PERI: orbital_elements[SMALL_BODY].p_longitude}
            )
            resonant_phase = cutoff_angle(resonant_phase)
            resonance_data = "%f %f %s %s %s\n" % (
                orbital_elements[SMALL_BODY].time, resonant_phase,
                orbital_elements[SMALL_BODY].serialize_as_asteroid(),
                orbital_elements[FIRST_BODY].serialize_as_planet(),
                orbital_elements[SECOND_BODY].serialize_as_planet()
            )
            yield resonance_data
