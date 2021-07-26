#!/usr/bin/env python3

#
# dice.py
# Author: Patrick Bannister
# Class to simulate dice using L7R homebrew rules.
#

import random


class Dice(object):
  '''
  Dice: class to simulate rolling dice under L7R rules.
  '''
  def __init__(self, rolled, faces=10, explode=True):
    '''
      rolled (int): number of dice to roll
      faces (int): number of faces on the die (maximum result)
      explode (bool): whether to reroll when the number of faces is
                      rolled
    '''
    self.rolled = rolled
    self.faces = faces
    self.explode = explode

  def _die_roll(self):
    '''
    _die_roll() -> int
    Return an int simulating a roll of a die with the specified number
    of faces.
    An "exploding" die adds to the result through recursion if the
    number of faces is rolled.
    '''
    roll = random.randint(1, self.faces)
    if (self.explode and (roll == self.faces)):
      return roll + self._die_roll()
    else:
      return roll

  def roll(self):
    '''
    roll() -> list of ints
    Return a list of ints simulating rolling dice.
    '''
    return [self._die_roll() for n in range(self.rolled)]

