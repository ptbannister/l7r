#!/usr/bin/env python3

#
# roll.py
# Author: Patrick Bannister
# Class to roll dice using L7R homebrew rules.
#


from dice.dice import Dice
from dice.mutator import DefaultMutator

default_mutator = DefaultMutator


class Roll(object):
  def __init__(self, rolled, kept, mutator_class=default_mutator, faces=10, explode=True):
    self.rolled = rolled
    self.kept = kept
    self.mutator = mutator_class(rolled, kept)
    self.faces = faces
    self.explode = explode
    self.dice = Dice(rolled, faces, explode)

  def roll(self):
    return self.mutator.mutate(self.dice.roll())

