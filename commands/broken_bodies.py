from entities.body import BrokenAsteroid
from entities.dbutills import session


def show_broken_bodies():
    items = session.query(BrokenAsteroid).order_by(BrokenAsteroid.name).all()
    for item in items:
        print(item.name)
