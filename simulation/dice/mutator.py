#!/usr/bin/env python3

#
# mutator.py
# Author: Patrick Bannister
# Implement mutators for dice rolls to simulate school abilities
# in L7R homebrew rules.
#

import random

from dice.dice import Dice


VALID_MUTATOR_NAMES = ['merchant', 'shosuro']


class DefaultMutator(object):
  def __init__(self, rolled, kept):
    self.rolled = rolled
    self.kept = kept

  def mutate(self, pool):
    '''
    mutate(pool) -> (int, int)
  
    Calculate the sum of the kept highest valued dice in the pool.
  
    Return a tuple of ints where the first element is the result,
    and the second element is the value of the mutator.
    '''
    result = sum(sorted(pool, reverse=True)[:self.kept])
    return (result, 0)


default_mutator_class = DefaultMutator


class MerchantMutator(object):
  def __init__(self, rolled, kept):
    self.rolled = rolled
    self.kept = kept
    self.unkept = rolled - kept

  def mutate(self, pool):
    '''
    mutate(pool) -> (int, int)
      pool (list): list of ints of die roll results
  
    Calculate the sum of the kept highest valued dice in the pool,
    after rerolling any number of dice in the pool.
  
    Return a tuple of ints where the first element is the result,
    and the second element is the value of the mutator.
    '''
    # sort pool in descending order
    pool.sort(reverse=True)
    # calculate normal result
    default = sum(pool[:self.kept])
    # pick dice to reroll
    reroll = self.optimize(pool)
    # drop rerolled dice
    for die in reroll:
      pool.remove(die)
    # reroll and add the new dice to the pool
    rerolled_dice = Dice(len(reroll)).roll()
    pool.extend(rerolled_dice)
    # sort pool in descending order calculate new result
    pool.sort(reverse=True)
    result = sum(pool[:self.kept])
    # calculate value of mutator
    bonus = result - default
    return (result, bonus)

  def optimize(self, pool):
    '''
    optimize(pool) -> list of ints
      pool (list of ints): rolled dice to optimize
  
    Return a list of the dice that should be rerolled with the
    merchant mutator. Optimize for the best result.
    '''
    # sort dice in ascending order
    pool.sort()
    # reroll all unkept dice
    reroll = pool[:self.unkept]
    # reroll all kept dice worth 5 or less
    for die in pool[self.unkept:]:
      if (die <= 5):
        reroll.append(die)
    return reroll


class ShosuroMutator(object):
  def __init__(self, rolled, kept):
    self.rolled = rolled
    self.kept = kept
    self.n_lowest = min(3, self.rolled - self.kept)

  def mutate(self, pool):
    '''
    shosuro_mutator(rolled, kept, pool) -> (int, int)
      rolled (int): number of rolled dice
      kept (int): number of kept dice
      pool (list): list of ints of die roll results
  
    Calculate the sum of the kept highest valued dice in the pool,
    plus the three lowest unkept dice.
  
    Return a tuple of ints where the first element is the result,
    and the second element is the value of the mutator.
    '''
    pool.sort(reverse=True)
    # calculate normal result
    default = sum(pool[:self.kept])
    # calculate value of mutator
    bonus = 0
    if (self.n_lowest > 0):
      bonus = sum(pool[(-1 * self.n_lowest):])
    return (default + bonus, bonus)

