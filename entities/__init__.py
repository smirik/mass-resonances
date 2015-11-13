from typing import List


class Body(object):
    pass


class Asteroid(Body):
    number = None
    resonance = None

    def __init__(self, number: int, resonance: List[float] = None):
        self.resonance = resonance
        self.number = number
