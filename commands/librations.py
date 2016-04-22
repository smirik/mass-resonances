from entities import Libration
from entities import ThreeBodyResonance
from entities.dbutills import session
from sqlalchemy.orm import joinedload
from texttable import Texttable


def show_librations():
    librations = session.query(Libration).options(
        joinedload('resonance'), joinedload('first_planet_name'), joinedload('second_planet_name')
    ).join(ThreeBodyResonance).join()

    table = Texttable(max_width=120)
    table.set_cols_width([10, 10, 10, 30, 15])
    table.add_row(['First planet',
                   'Second second',
                   'Asteroid',
                   'Integers and semi major axis of asteroid',
                   'apocentric'])
    for libration in librations:
        table.add_row([libration.first_planet_name,
                       libration.second_planet_name,
                       libration.resonance.small_body.name,
                       libration.resonance,
                       '%sapocentric' % 'not ' if not libration.is_apocentric else '', ])

    print(table.draw())
