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
import shutil

from simulation.bayushi_school import BayushiBushiSchool
from simulation.character import Character
from simulation.character_file import CharacterReader
from simulation.context import EngineContext
from simulation.engine import CombatEngine
from simulation.features import write_feature_file_header, SummaryFeatures
from simulation.groups import Group
from simulation.groups_file import GroupsReader
from simulation.log import logger

LOG_LEVELS = {
  'critical': logging.CRITICAL,
  'error': logging.ERROR,
  'fatal': logging.FATAL,
  'warn': logging.WARN,
  'info': logging.INFO,
  'debug': logging.DEBUG
}

MAX_TRIALS = 1000

script_path = os.path.realpath(__file__)
script_dirpath = os.path.split(script_path)[0]  


def error(msg):
  logger.error(msg)
  print(msg)


def load_characters(dirpath):
  '''
  load_characters(dirpath) -> dict
    dirpath (str): path to directory containing groups.yaml and character files

  Returns a dictionary of str:Character mappings pairing character names with Character objects.
  '''
  fnames = os.listdir(dirpath)
  fnames.remove('groups.yaml')
  characterd = {}
  for fname in fnames:
    fpath = os.path.join(dirpath, fname)
    if not os.path.isfile(fpath):
      logger.warn('Skipping invalid input file: {}'.format(fpath))
      continue
    with open(fpath, 'r') as f:
      character = CharacterReader().read(f)
      characterd[character.name()] = character
  return characterd


def load_groups(dirpath, characterd):
  '''
  load_groups(dirpath, characterd) -> list of Group
    dirpath (str): path to directory containing groups.yaml and character files
    characterd (dict): dictionary loaded with str:Character mappings of names to characters

  Returns the list of groups for this simulation.
  
  The control group will be the first group in the list.
  '''
  fpath = os.path.join(dirpath, 'groups.yaml')
  if not os.path.exists(fpath):
    logger.error('groups.yaml not found in input directory {}'.format(dirpath))
    sys.exit(1)
  with open(fpath, 'r') as f:
    return GroupsReader().read(f, characterd)
  

def setup_groups(dirpath):
  '''
  setup_groups(dirpath) -> list of Group
    dirpath (str): path to directory containing yroups.yaml and character files

  Returns a list of groups of characters for this simulation,
  generated by reading the yaml files in the given dirpath.

  The control group will be the first group in the list.
  '''
  characters = load_characters(dirpath)
  return load_groups(dirpath, characters)


def main():
  argparser = ap.ArgumentParser()
  argparser.add_argument('-i', '--input-dirpath', help='path to directory containing characters and group definitions', type=str, required=True)
  argparser.add_argument('-o', '--output-dirpath', help='path to directory where output features will be written', type=str, default=os.path.join(script_dirpath, 'output'))
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
    error('May not run trials < 0')
    sys.exit(1)
  elif ntrials > MAX_TRIALS:
    error('May not run trials > 0')
    sys.exit(1)

  # validate character and group data
  if not os.path.isdir(args.input_dirpath):
    error('Invalid input directory path {}'.format(args.input_dirpath))
    sys.exit(1)

  # set up characters and group data
  groups = setup_groups(args.input_dirpath)

  # validate output dirpath
  if not os.path.exists(args.output_dirpath):
    os.mkdir(args.output_dirpath)
  else:
    if not os.path.isdir(args.output_dirpath):
      error('Output directory already exists but is not a directory: {}'.format(args.output_dirpath))
      sys.exit(1)

  # set up feature file
  feature_path = os.path.join(args.output_dirpath, 'features.txt')

  # set up engine
  context = EngineContext(groups)
  context.initialize()
  engine = CombatEngine(context)

  test_victories = 0

  # open feature file (gathers data about trials)
  with open(feature_path, 'w') as feature_file:
    # write header for feature file
    write_feature_file_header(feature_file)
    # run trials
    for i in range(ntrials):
      # run trial
      engine.run()
      # collect and write features
      features = context.features()
      context.features().complete(context)
      context.features().write(feature_file)
      # observe winner
      if features.winner() == 1:
        test_victories += 1
      # reset for next trial
      engine.reset()

  # Print test group win rate
  test_group_characters = ', '.join([character.name() for character in groups[1]])
  print('Test group ({}) won {}/{} trials.'.format(test_group_characters, test_victories, ntrials))

  report_results(feature_path, ntrials)


def report_results(feature_fpath, ntrials):
  # summarize collected features
  summary = SummaryFeatures()
  summary.summarize(feature_fpath, ntrials)

  # write summary report
  summary.print_report()


if __name__ == '__main__':
  main()

