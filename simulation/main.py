#!/usr/bin/env python3

#
# main.py
# Author: Patrick Bannister (ptbanni@gmail.com)
#
# Driver for L7R combat simulator.
#

import argparse as ap
import logging
import os

from simulation.bayushi_school import BayushiBushiSchool
from simulation.character import Character
from simulation.context import EngineContext
from simulation.engine import CombatEngine
from simulation.groups import Group
from simulation.log import logger

LOG_LEVELS = {
  'critical': logging.CRITICAL,
  'error': logging.ERROR,
  'fatal': logging.FATAL,
  'warn': logging.WARN,
  'debug': logging.DEBUG
}

MAX_TRIALS = 1000


def load_characters():
  # TODO: load characters from YAML or JSON or something
  akodo = Character('Akodo')
  akodo.set_ring('air', 3)
  akodo.set_ring('earth', 3)
  akodo.set_ring('fire', 3)
  akodo.set_ring('water', 3)
  akodo.set_ring('void', 3)
  akodo.set_skill('attack', 3)
  #akodo.set_skill('double attack', 5)
  akodo.set_skill('parry', 4)
  bayushi = Character('Bayushi')
  bayushi.set_ring('air', 3)
  bayushi.set_ring('earth', 3)
  bayushi.set_ring('fire', 3)
  bayushi.set_ring('water', 3)
  bayushi.set_ring('void', 3)
  bayushi.set_skill('attack', 4)
  #bayushi.set_skill('double attack', 5)
  #bayushi.set_skill('feint', 5)
  #bayushi.set_skill('iaijutsu', 5)
  bayushi.set_skill('parry', 5)
  bayushi_school = BayushiBushiSchool()
  #bayushi_school.apply_special(bayushi)
  #bayushi_school.apply_rank_one_ability(bayushi)
  #bayushi_school.apply_rank_two_ability(bayushi)
  #bayushi_school.apply_rank_three_ability(bayushi)
  #bayushi_school.apply_rank_four_ability(bayushi)
  #bayushi_school.apply_rank_five_ability(bayushi)
  return [Group([akodo]), Group([bayushi])]


def main():
  argparser = ap.ArgumentParser()
  argparser.add_argument('-t', '--trials', help='How many trials to run', type=int, default=100)
  argparser.add_argument('--log-level', help='Log level to use', choices=[k for k in LOG_LEVELS.keys()], default='error')
  argparser.add_argument('--log-path', help='Path to write logs', type=str, default=os.path.join(os.getcwd(), 'simulation.log'))

  args = argparser.parse_args()

  # reset log file
  if os.path.exists(args.log_path):
    os.unlink(args.log_path)

  # log to file
  logging.basicConfig(filename=args.log_path, level=LOG_LEVELS[args.log_level])

  # validate number of trials
  ntrials = args.trials
  if ntrials < 0:
    logger.error('May not run trials < 0')
    sys.exit(1)
  elif ntrials > MAX_TRIALS:
    logger.error('May not run trials > 0')
    sys.exit(1)

  # set up simulation
  groups = load_characters()

  # set up engine
  context = EngineContext(groups)
  context.initialize()
  engine = CombatEngine(context)

  test_victories = 0

  for i in range(ntrials):
    engine.run()
    features = context.features()
    if features.get_winner() == 1:
      test_victories += 1
    engine.reset()

  test_group_characters = ', '.join([character.name() for character in groups[1]])
  print('Test group ({}) won {}/{} trials.'.format(test_group_characters, test_victories, ntrials))

if __name__ == '__main__':
  main()

