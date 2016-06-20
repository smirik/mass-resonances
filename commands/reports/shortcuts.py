class AsteroidCondition:
    def __init__(self, start, stop):
        self.stop = stop
        self.start = start


class PlanetCondition:
    def __init__(self, first_planet_name: str = None, second_planet_name: str = None):
        self.second_planet_name = second_planet_name
        self.first_planet_name = first_planet_name


class AxisInterval:
    def __init__(self, start: float, stop: float):
        self.stop = stop
        self.start = start


class ResonanceIntegers:
    def __init__(self, first, second, third):
        self.third = third
        self.second = second
        self.first = first