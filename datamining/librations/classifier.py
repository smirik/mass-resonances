from typing import List, Dict
import logging

from .librationbuilder import ApocentricBuilder
from .librationbuilder import TransientBuilder
from .librationbuilder import LibrationDirector
from datamining import ResonanceOrbitalElementSetFacade
from entities import Libration
from entities import ThreeBodyResonance
from entities.body import PlanetName
from entities.dbutills import session
from settings import Config
from sqlalchemy import or_

CONFIG = Config.get_params()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']


class LibrationClassifier:
    """
    Class is need for determining type of libration. If it needs, class will build libration by
    resonances and orbital elements of related sky bodies.
    """
    def __init__(self, get_from_db, bodyname1, bodyname2):
        self._bodyname1, self._bodyname2 = bodyname1, bodyname2
        self._get_from_db = get_from_db
        bodynames = session.query(PlanetName).filter(
            or_(PlanetName.name == bodyname1, PlanetName.name == bodyname2)).all()
        bodyname1 = [x for x in bodynames if x.name == bodyname1][0]
        bodyname2 = [x for x in bodynames if x.name == bodyname2][0]
        self._libration_director = LibrationDirector(bodyname1, bodyname2)
        self._resonance = None  # type: ThreeBodyResonance
        self._resonance_str = None  # type: str
        self._asteroid_num = None  # type: int
        self._libration = None  # type: Libration

    def set_resonance(self, resonance: ThreeBodyResonance):
        """
        Wroks as hook before classifying libration. It is need for saving useful data before any
        actions on resonance's libration by SQLalchemy, because we can try get something from
        resonance, and doesn't allow us remove libration.
        :param resonance:
        """
        self._resonance = resonance
        self._resonance_str = str(resonance)
        self._asteroid_num = self._resonance.asteroid_number
        librations = [x for x in self._resonance.librations if (
            x.first_planet_name.name == self._bodyname1 and
            x.second_planet_name.name == self._bodyname2
        )]
        self._libration = librations[0] if librations else None

    def classify(self, orbital_elem_set: ResonanceOrbitalElementSetFacade,
                 serialized_phases: List[Dict[str, float]]) -> bool:
        """
        Determines class of libration. Libration can be loaded from database if object has upped
        flag _get_from_db. If libration's class was not determined, libration will be removed and
        method returns False else libration will be saved and method return True.
        :param serialized_phases:
        :param orbital_elem_set:
        :return: flag of successful determining class of libration.
        """
        if not self._get_from_db and self._libration is None:
            builder = TransientBuilder(self._resonance, orbital_elem_set, serialized_phases)
            self._libration = self._libration_director.build(builder)
        elif not self._libration:
            return True

        try:
            if _save_as_transient(self._libration, self._resonance, self._asteroid_num,
                                  self._resonance_str):
                return True
            elif not self._libration.is_apocentric:
                logging.info('A%i, pure resonance %s', self._asteroid_num, self._resonance_str)
                return True
            raise _NoTransientException()
        except _NoTransientException:
            if not self._get_from_db and not self._libration.is_apocentric:
                builder = ApocentricBuilder(self._resonance, orbital_elem_set, serialized_phases)
                self._libration = self._libration_director.build(builder)

            if self._libration.is_pure:
                logging.info('A%i, pure apocentric resonance %s', self._asteroid_num,
                             self._resonance_str)
                return True
            else:
                session.expunge(self._libration)
        return False


def _save_as_transient(libration: Libration, resonance: ThreeBodyResonance, asteroid_num: int,
                       resonance_str: str):
    if not libration.is_pure:
        if libration.is_transient:
            if libration.percentage:
                logging.info('A%i, %s, resonance = %s', asteroid_num,
                             str(libration), str(resonance))
                return True
            else:
                logging.debug(
                    'A%i, NO RESONANCE, resonance = %s, max = %f',
                    asteroid_num, resonance_str, libration.max_diff
                )
                session.expunge(libration)
                raise _NoTransientException()
        raise _NoTransientException()
    return False


class _NoTransientException(Exception):
    pass

