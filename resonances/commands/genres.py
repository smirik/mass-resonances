from os import mkdir, getcwd
from os.path import exists
from os.path import join as opjoin
from typing import Tuple, List

from resonances.datamining import PhaseBuilder, PhaseStorage, build_bigbody_elements, \
    ResonanceOrbitalElementSetFacade, PhaseLoader, PhaseCleaner
from resonances.datamining.orbitalelements import FilepathBuilder
from resonances.datamining.resonances import AEIDataGetter
from resonances.datamining.resonances import get_resonances_by_asteroids

from resonances.entities import ResonanceMixin

from .plot import ResfileMaker


def _make_res(by_resonance: ResonanceMixin, filepaths: List[str],
              planets: tuple, integers: List[str]):
    asteroid_name = by_resonance.small_body.name
    resonance_id = by_resonance.id
    phase_storage = PhaseStorage.file
    phase_builder = PhaseBuilder(phase_storage)
    phase_loader = PhaseLoader(phase_storage)
    phase_cleaner = PhaseCleaner(phase_storage)

    print('Loading aei files.')
    builder = FilepathBuilder(filepaths, True)
    planet_aei_paths = [builder.build('%s.aei' % x) for x in planets]
    resmaker = ResfileMaker(planets, planet_aei_paths)
    getter = AEIDataGetter(builder)
    orbital_element_sets = build_bigbody_elements(planet_aei_paths)
    orbital_elem_set_facade = ResonanceOrbitalElementSetFacade(orbital_element_sets, by_resonance)

    aei_data = getter.get_aei_data(asteroid_name)
    phase_builder.build(aei_data, resonance_id, orbital_elem_set_facade)
    phases = phase_loader.load(resonance_id)

    folder = opjoin(getcwd(), 'res')
    if not exists(folder):
        mkdir(folder)
    resmaker.make(phases, aei_data, opjoin(
        folder, '%s_%s_%s.res' % (asteroid_name, '_'.join(planets),
                                  '_'.join([str(x) for x in integers]))
    ))
    phase_cleaner.delete(resonance_id)


def genres(asteroids: tuple, integers: List[str], filepaths: List[str], planets: Tuple):
    resonances = get_resonances_by_asteroids(asteroids, False, integers, planets)
    for resonance in resonances:
        _make_res(resonance, filepaths, planets, integers)
