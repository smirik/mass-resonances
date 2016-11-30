from resonances.entities.dbutills import session

from resonances.entities.body import BrokenAsteroid


def show_broken_bodies():
    items = session.query(BrokenAsteroid).order_by(BrokenAsteroid.name).all()
    for item in items:
        print(item.name)
