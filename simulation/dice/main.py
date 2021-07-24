#!/usr/bin/env python3

#
# main.py
# Author: Patrick Bannister
# Driver for a Monte Carlo simulation to calculate the probability
# of rolling ascending Target Numbers using the L7R homebrew rules.
#

import argparse as ap
import multiprocessing as mp
import random


from dice.dice import Dice
from dice.mutator import MerchantMutator, ShosuroMutator, VALID_MUTATOR_NAMES, default_mutator_class


USAGE_STR = '''python dice.py [--mutator MUTATOR_NAME] [--trials N_TRIALS]
  --trials N_TRIALS: run specified number of trials (default 100,000)
  --mutator MUTATOR_NAME: apply a mutator for a school special ability.
    Known mutator names:
    merchant: Merchant School mutator (allows rerolling some dice)
    shosuro: Shosuro Actor School (add up to three lowest unkept dice)
'''


class Simulation:
  def __init__(self, rolled, kept, step=5, bins=15, trials=100000, mutator_class=default_mutator_class):
    self.rolled = rolled
    self.kept = kept
    self.step = step
    self.bins = bins
    self.trials = trials
    self.dice = Dice(rolled, kept, mutator_class)
    self.bins = bins
    self.results = [0 for i in range(bins)]
    self.mutator_value = 0
    self.mutator_value_squares = 0
   
  def run(self):
    for n in range(self.trials):
      (roll, bonus) = self.dice.roll()
      self.results[min(int(roll / self.step), self.bins-1)] += 1
      self.mutator_value += bonus
      self.mutator_value_squares += bonus*bonus

  def __eq__(self, other):
    if (not isinstance(other, Simulation)):
      raise NotImplementedError
    return (self.rolled == other.rolled) and (self.kept == other.kept)

  def __lt__(self, other):
    if (not isinstance(other, Simulation)):
      raise NotImplementedError
    if (self.rolled == other.rolled):
      return self.rolled < other.rolled
    else:
      return self.rolled < other.rolled


def run_simulation(rolled, kept, step=5, bins=15, trials=100000, mutator_class=default_mutator_class):
  simulation = Simulation(rolled, kept, step, bins, trials, mutator_class)
  simulation.run()
  return simulation


def main():
  argparser = ap.ArgumentParser()
  argparser.add_argument('--mutator', choices=VALID_MUTATOR_NAMES, help='Mutator to use for simulating school abilities', type=str, default=None)
  argparser.add_argument('--trials', help='Number of trials for each dice pool', type=int, default=100000)
  args = argparser.parse_args()

  nprocesses = mp.cpu_count()
  step = 5
  bins = 15
  trials = args.trials
  mutator_name = args.mutator
  if (mutator_name == 'merchant'):
    mutator_class = MerchantMutator
  elif (mutator_name == 'shosuro'):
    mutator_class = ShosuroMutator
  elif (mutator_name == None):
    mutator_class = default_mutator_class

  simulations = []
  with mp.Pool(processes=nprocesses) as pool:
    # build list of parameters for simulations of all possible dice pools
    params = []
    for rolled in range(1, 11):
      params.extend([(rolled, kept, step, bins, trials, mutator_class) for kept in range(1, rolled + 1)])

    # run simulations
    async_results = [pool.apply_async(run_simulation, t) for t in params]
    simulations = [result.get(None) for result in async_results]

  # output results
  simulations.sort()
  header = '\t' + '\t'.join([str(i*step) for i in range(1, bins)]) + '\tMutator Value'
  print(header)
  prev_rolled = 0
  for simulation in simulations:
    if (simulation.rolled != prev_rolled):
      print()
      prev_rolled = simulation.rolled
    probabilities = []
    for i in range(1, bins):
      probabilities.append(sum(simulation.results[i:bins]) / trials)
    probabilities_str = '\t'.join(['{:.2f}'.format(p) for p in probabilities])
    mutator_value = '{:.2f}'.format(simulation.mutator_value / trials)
    print('{}k{}\t{}\t{}'.format(simulation.rolled, simulation.kept, probabilities_str, mutator_value))

