import logging
from typing import List, Dict

from resonances.datamining import ResonanceOrbitalElementSetFacade
from resonances.entities import ResonanceMixin, BodyNumberEnum, LibrationMixin

from resonances.entities.dbutills import session
from resonances.settings import Config
from .librationbuilder import ApocentricBuilder
from .librationbuilder import LibrationDirector
from .librationbuilder import TransientBuilder

CONFIG = Config.get_params()
BODIES_COUNTER = CONFIG['integrator']['number_of_bodies']


class LibrationClassifier:
    """
    Class is need for determining type of libration. If it needs, class will build libration by
    resonances and orbital elements of related sky bodies.
    """
    def __init__(self, get_from_db, body_count: BodyNumberEnum):
        self._get_from_db = get_from_db
        self._libration_director = LibrationDirector(body_count)
        self._resonance = None  # type: ResonanceMixin
        self._resonance_str = None  # type: str
        self._asteroid_num = None  # type: int
        self._libration = None  # type: Libration

    def set_resonance(self, resonance: ResonanceMixin):
        """
        Wroks as hook before classifying libration. It is need for saving useful data before any
        actions on resonance's libration by SQLalchemy, because we can try get something from
        resonance, and doesn't allow us remove libration.
        :param resonance:
        """
        self._resonance = resonance
        self._resonance_str = str(resonance)
        self._asteroid_num = self._resonance.asteroid_number
        self._libration = self._resonance.libration

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


def _save_as_transient(libration: LibrationMixin, resonance: ResonanceMixin, asteroid_num: int,
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
