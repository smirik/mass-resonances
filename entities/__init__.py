from typing import List

from entities.body import _Body, LONG, PERI, LONG_COEFF, PERI_COEFF
from entities.dbutills import Base
from .phase import Phase
from .libration import Libration
from .threebodyresonance import LONG
from .threebodyresonance import LONG_COEFF
from .threebodyresonance import PERI
from .threebodyresonance import PERI_COEFF
from .threebodyresonance import ThreeBodyResonance
from .threebodyresonance import build_resonance


class RDB_Asteroid(_Body):
    number = None
    resonance = None

    def __init__(self, number: int, resonance: List[float] = None):
        self.resonance = resonance
        self.number = number


