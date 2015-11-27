#!/usr/bin/env python
from cli import cli
from entities import Body, Libration
from entities import ThreeBodyResonance
from entities.dbutills import session

__verion__ = '0.0.1'

if __name__ == '__main__':
    # first_body = Body(name='qwe', longitude_coeff=1, perihelion_longitude_coeff=2)
    # second_body = Body(name='asd', longitude_coeff=1, perihelion_longitude_coeff=2)
    # small_body = Body(name='zxc', longitude_coeff=1, perihelion_longitude_coeff=2)
    #
    # session.add(first_body)
    # session.add(second_body)
    # session.add(small_body)
    #
    # resonance = ThreeBodyResonance(
    #     first_body=first_body,
    #     second_body=second_body,
    #     small_body=small_body,
    #     asteroid_axis=1
    # )
    # session.add(resonance)
    # session.commit()
    # # resonance = ThreeBodyResonance()
    # # resonance.first_body = first_body
    #
    # libration = Libration()
    # libration._resonance = resonance
    # # libration._average_delta = 1
    #
    # print(session.new)
    # session.delete(resonance)
    # session.delete(first_body)
    # session.delete(second_body)
    # session.delete(small_body)
    # session.commit()
    # pass
    cli()
