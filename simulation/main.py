#!/usr/bin/env python3

#
# main.py
# Author: Patrick Bannister (ptbanni@gmail.com)
#
# Driver for L7R combat simulator.
#

import argparse as ap
import logging

from simulation.character import Character
from simulation.context import EngineContext
from simulation.engine import CombatEngine
from simulation.groups import Group
from simulation.log import logger

LOG_LEVELS = {
  'critical': logging.CRITICAL,
  'error': logging.ERROR,
  'fatal': logging.FATAL,
  'warn': logging.WARN
}

MAX_TRIALS = 1000


def load_characters():
  # TODO: load characters from YAML or JSON or something
  akodo = Character('Akodo')
  akodo.set_ring('air', 3)
  akodo.set_ring('earth', 5)
  akodo.set_ring('fire', 5)
  akodo.set_ring('water', 6)
  akodo.set_ring('void', 5)
  akodo.set_skill('attack', 4)
  akodo.set_skill('parry', 5)
  bayushi = Character('Bayushi')
  bayushi.set_ring('air', 3)
  bayushi.set_ring('earth', 5)
  bayushi.set_ring('fire', 6)
  bayushi.set_ring('water', 5)
  bayushi.set_ring('void', 5)
  bayushi.set_skill('attack', 4)
  bayushi.set_skill('parry', 5)
  return [Group([akodo]), Group([bayushi])]


def main():
  argparser = ap.ArgumentParser()
  argparser.add_argument('-t', '--trials', help='How many trials to run', type=int, default=100)
  argparser.add_argument('--log-level', help='Log level to use', choices=[k for k in LOG_LEVELS.keys()], default='error')

  args = argparser.parse_args()

  # set log level
  logger.setLevel(LOG_LEVELS[args.log_level])

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
  context.load_probability_data()
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

