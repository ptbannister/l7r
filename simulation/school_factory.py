#!/usr/bin/env python3

#
# school_factory.py
# Author: Patrick Bannister (ptbanni@gmail.com)
# Character Schools for L7R combat simulator.
#

from simulation.akodo_school import AkodoBushiSchool
from simulation.bayushi_school import BayushiBushiSchool


def get_school(name):
  if name == 'Akodo Bushi School':
    return AkodoBushiSchool()
  elif name == 'Bayushi Bushi School':
    return BayushiBushiSchool()
  else:
    raise ValueError('Unsupported school: {}'.format(name))

