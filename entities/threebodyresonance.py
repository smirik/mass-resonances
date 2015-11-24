from typing import List
from typing import Dict

LONG = 'longitude'
PERI = 'perihelion_%s' % LONG
LONG_COEFF = '%s_coeff' % LONG
PERI_COEFF = '%s_coeff' % PERI


class ThreeBodyResonance:
    """ Represents three body resonance. Stores coeffitients that satisfy rule
    D'Alambert and axis of related asteroid.
    """
    def __init__(self, first_body: Dict[str, int], second_body: Dict[str, int],
                 small_body: Dict[str, int], asteroid_axis: float):
        self._asteroid_axis = asteroid_axis
        self._small_body = small_body
        self._second_body = second_body
        self._first_body = first_body

    @property
    def asteroid_axis(self):
        return self._asteroid_axis

    def __str__(self):
        return '[%i %i %i %i %i %i %f]' % (
            self._first_body[LONG_COEFF],
            self._second_body[LONG_COEFF],
            self._small_body[LONG_COEFF],
            self._first_body[PERI_COEFF],
            self._second_body[PERI_COEFF],
            self._small_body[PERI_COEFF],
            self._asteroid_axis
        )

    def get_resonant_phase(self, first_body: Dict[str, float],
                           second_body: Dict[str, float],
                           small_body: Dict[str, float]) -> float:
        """Computes resonant phase by linear combination of stored coeffitients
        and pointed longitudes.

        :param first_body:
        :param second_body:
        :param small_body:
        :return:
        """
        return (self._first_body[LONG_COEFF] * first_body[LONG] +
                self._first_body[PERI_COEFF] * first_body[PERI] +
                self._second_body[LONG_COEFF] * second_body[LONG] +
                self._second_body[PERI_COEFF] * second_body[PERI] +
                self._small_body[LONG_COEFF] * small_body[LONG] +
                self._small_body[PERI_COEFF] * small_body[PERI])


def build_resonance(data: List[str]) -> ThreeBodyResonance:
    """Builds instance of ThreeBodyResonance by passed list of string values.

    :param data:
    :return:
    """
    first_body = {
        LONG_COEFF: int(data[0]),
        PERI_COEFF: int(data[3])
    }
    second_body = {
        LONG_COEFF: int(data[1]),
        PERI_COEFF: int(data[4])
    }
    small_body = {
        LONG_COEFF: int(data[2]),
        PERI_COEFF: int(data[5])
    }
    return ThreeBodyResonance(first_body, second_body, small_body, float(data[6]))
