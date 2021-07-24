#!/usr/bin/env python3

#
# dice.py
# Author: Patrick Bannister
# Class to roll dice using L7R homebrew rules.
#

import random


from dice.mutator import DefaultMutator


default_mutator = DefaultMutator


class Dice(object):
  def __init__(self, rolled, kept, mutator_class=default_mutator, faces=10, explode=True):
    self.rolled = rolled
    self.kept = kept
    self.mutator = mutator_class(rolled, kept)
    self.faces = faces
    self.explode = explode

  def _die(self):
    roll = random.randint(1, self.faces)
    if (self.explode and (roll == self.faces)):
      return roll + self._die()
    else:
      return roll

  def roll(self):
    pool = [self._die() for n in range(self.rolled)]
    return self.mutator.mutate(pool)

