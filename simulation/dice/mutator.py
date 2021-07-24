#!/usr/bin/env python3

#
# mutator.py
# Author: Patrick Bannister
# Implement mutators for dice rolls to simulate school abilities
# in L7R homebrew rules.
#

import random

VALID_MUTATOR_NAMES = ['merchant', 'shosuro']

# map pool sizes to the maximum value worth rerolling with the
# merchant mutator on that pool size
MERCHANT_OPTIMIZER_MAP = {
  1: 5,
  2: 5,
  3: 5,
  4: 5,
  5: 5,
  6: 5,
  7: 11,
  8: 11,
  9: 11,
  10: 11
}


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
    self.n_lowest = rolled - kept 

  @staticmethod
  def merchant_constraint(n):
    '''
    merchant_constraint(n) -> int
      n (int): number of dice
  
    Returns the minimum of the sum of the values of n dice that would
    be rerolled with the merchant mutator.
    '''
    return 5 * (n - 1)

  def mutate(self, pool):
    '''
    mutate(pool) -> (int, int)
      pool (list): list of ints of die roll results
  
    Calculate the sum of the kept highest valued dice in the pool,
    rerolling the N lowest valued dice in the pool, where the sum of
    the values of the N dice is greater than or equal to 5*(N-1).
    This means you may reroll the lowest die without restriction,
    or the lowest two dice whose combined value is 5, or the lowest
    three dice whose combined value is 10, etc.
  
    Return a tuple of ints where the first element is the result,
    and the second element is the value of the mutator.
    '''
    pool.sort(reverse=True)
    # calculate normal result
    default = sum(pool[:self.kept])
    # calculate value of mutator
    bonus = 0
    return (default, 0)

  def optimizer(self, pool):
    '''
    optimizer(rolled, kept, pool) -> int
  
    Calculate the optimal number of dice to reroll with the merchant
    mutator.
    '''
    # sort dice in ascending value order
    pool = sorted(pool)
    reroll = 0
    # if there are unkept dice, reroll at least that many dice, if possible
    if (self.unkept > 0):
      # sort unkept dice in descending order
      unkept_pool = sorted(pool[:self.unkept], reverse=True)
      reroll = self.unkept
      # reroll as many unkept dice as possible
      # drop low dice if the constraint is unsatisfied
      while (merchant_constraint(reroll) > sum(pool[:reroll])):
        reroll -= 1
    # TODO: figure out how to optimize rerolling kept dice
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

