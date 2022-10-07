#!/usr/bin/env python3

#
# advantages.py
#
# Defines advantages that a character may buy in the L7R combat simulator.
#

ADVANTAGES = {
  'charming': 2,
  'discerning': 5,
  'fierce': 2,
  'genealogist': 2,
  'great destiny': 8,
  'higher purpose': 2,
  'imperial favor': 2,
  'kind eye': 3,
  'lucky': 5,
  'quick healer': 3,
  'specialization': 2,
  'strength of the earth': 8,
  'tactician': 2,
  'virtue': 3,
  'wealthy': 2,
  'worldly': 4
}

class Advantage(object):
  def __init__(self, name):
    if name not in ADVANTAGES.keys():
      raise ValueError('{} is not a valid Advantage'.format(name))
    self._name = name

  def cost(self):
    return ADVANTAGES[self.name()]

  def name(self):
    return self._name

