#!/usr/bin/env python3

#
# roll.py
# Author: Patrick Bannister
# Class to roll dice using L7R homebrew rules.
#


import random


def normalize_roll_params(rolled, kept, bonus=0):
  '''
  normalize_roll_params(rolled, kept, bonus=0) -> tuple of ints
    rolled (int): number of rolled dice
    kept (int): number of kept dice
    bonus (int): flat bonus to roll

  Returns normalized roll parameters, which is the tuple of
  (rolled, kept, bonus) for a roll.
  The algorithm is that excess rolled dice above ten become
  extra kept dice, excess kept dice above ten become a bonus,
  and the bonus is added to the roll.
  '''
  if rolled > 10:
    excess_rolled = rolled - 10
    rolled = 10
    kept += excess_rolled
  if kept > 10:
    excess_kept = kept - 10
    kept = 10
    bonus += excess_kept
  return (rolled, kept, bonus)


class TestDice(object):
  '''
  Die source that provides rigged dice for testing.
  Acts as a FIFO queue. You append or extend the die source with rolled dice (ints),
  and when a Roll gets results from this source, it pops the earliest queued results.
  '''
  def __init__(self):
    self._dice = []

  def extend(self, dice):
    '''
    extend(dice)
      dice: list of int

      Extend this die source's results with a list of rolled dice.
    '''
    self._dice.extend(dice)

  def append(self, die):
    '''
    append(die)
      die: int

      Append a rolled die to this die source.
    '''
    self._dice.append(die)

  def roll_die(self):
    return self._dice.pop(0)


class BaseRoll(object):
  def __init__(self, rolled, kept, faces=10, explode=True, die_source=None):
    # normalize roll parameters
    (self._rolled, self._kept, self._bonus) = normalize_roll_params(rolled, kept)
    # set die faces
    self._faces = faces
    # set exploding behavior
    self._explode = explode
    # set die source
    if die_source is not None:
      self._die_source = die_source
    else:
      self._die_source = self

  def roll_die(self):
    '''
    roll_die() -> int
    Return an int simulating a roll of a die with the specified number
    of faces.
    An "exploding" die adds to the result through recursion if the
    number of faces is rolled.
    '''
    result = random.randint(1, self._faces)
    if (self._explode and (result == self._faces)):
      return result + self._roll_die()
    else:
      return result

  def _roll_die(self):
    return self._die_source.roll_die()

  def set_die_source(self, die_source):
    self._die_source = die_source


class Roll(BaseRoll):
  def __init__(self, rolled, kept, faces=10, explode=True, die_source=None):
    super().__init__(rolled, kept, faces, explode, die_source)

  def roll(self):
    dice = [self._roll_die() for n in range(self._rolled)]
    dice.sort(reverse=True)
    return sum(dice[:self._kept]) + self._bonus


class InitiativeRoll(BaseRoll):
  def __init__(self, rolled, kept, faces=10, die_source=None):
    super().__init__(rolled, kept, faces, False, die_source)

  def roll(self):
    dice = sorted([self._roll_die() for n in range(self._rolled)])
    return dice[:self._kept]

