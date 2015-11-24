from typing import List

from .threebodyresonance import ThreeBodyResonance
from .threebodyresonance import LONG
from .threebodyresonance import PERI
from .threebodyresonance import LONG_COEFF
from .threebodyresonance import PERI_COEFF
from .threebodyresonance import build_resonance
from .libration import Libration


class Body(object):
    pass


class Asteroid(Body):
    number = None
    resonance = None

    def __init__(self, number: int, resonance: List[float] = None):
        self.resonance = resonance
        self.number = number


