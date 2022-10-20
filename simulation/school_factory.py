#!/usr/bin/env python3

#
# school_factory.py
#
# Factory function to get character Schools for L7R combat simulator from the name of the school.
#

from simulation.akodo_school import AkodoBushiSchool
from simulation.bayushi_school import BayushiBushiSchool
from simulation.shiba_school import ShibaBushiSchool


def get_school(name):
  if not isinstance(name, str):
    raise ValueError('get_school name parameter must be str')
  if name == 'Akodo Bushi School':
    return AkodoBushiSchool()
  elif name == 'Bayushi Bushi School':
    return BayushiBushiSchool()
  elif name == 'Shiba Bushi School':
    return ShibaBushiSchool()
  else:
    raise ValueError('Unsupported school: {}'.format(name))

