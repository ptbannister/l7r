#!/usr/bin/env python3

#
# features.py
#
#
# Observe and analyze features of an L7R simulation run.
#

import csv

from simulation import events
from simulation.skills import ATTACK_SKILLS

FIELDNAMES = [
  'winner',
  'control_sw_remaining',
  'control_vp_remaining',
  'test_sw_remaining',
  'test_vp_remaining',
  'duration_rounds',
  'duration_phases',
  'control_actions_taken',
  'control_attacks_taken',
  'control_parries_taken',
  'control_ap_remaining',
  'control_ap_spent',
  'control_ap_spent_wound_checks',
  'control_damage_rolls_count',
  'control_damage_rolls_sum',
  'control_damage_rolls_sumsquares',
  'control_sw',
  'control_vp_spent',
  'control_vp_spent_attacks',
  'control_vp_spent_wound_checks',
  'test_actions_taken',
  'test_attacks_taken',
  'test_parries_taken',
  'test_ap_remaining',
  'test_ap_spent',
  'test_ap_spent_wound_checks',
  'test_damage_rolls_count',
  'test_damage_rolls_sum',
  'test_damage_rolls_sumsquares',
  'test_sw',
  'test_vp_spent',
  'test_vp_spent_attacks',
  'test_vp_spent_wound_checks'
]


class SummaryFeatures(object):
  '''
  Summary of many simulation runs.

  Questions we might ask after a simulation:
  * Duration in rounds
  * Duration in phases
  * AP remaining
  * AP spent
  * VP remaining
  * VP spent
  * VP spent on attacks
  * VP spent on wound checks
  * Winner's normal initiative actions per round compared to loser
  * Winner's total SW compared to loser (at beginning of combat)
  * SW remaining (winner only)
  * Actions taken
  * Attacks taken
  * Parries taken
  * Interrupt actions taken
  * Interrupt attacks taken
  * Interrupt parries taken
  * Average damage per attack
  '''
  def __init__(self):
    self._control_victories = 0
    self._test_victories = 0
    # summary statistics
    self._summary = {}
    # common results
    self._data = {}
    # results given control group victory
    self._control_data = {}
    self._control_summary = {}
    # results given test group victory
    self._test_data = {}
    self._test_summary = {}
    self.initialize()

  def initialize(self):
    for field in FIELDNAMES:
      self._data[field] = 0
      self._control_data[field] = 0
      self._test_data[field] = 0

  def observe(self, trial_features):
    if trial_features.get_winner() == -1:
      self._control_victories += 1
    else:
      self._test_victories += 1

  def mean(self, total, n):
    if n == 0:
      return 0
    else:
      return total / n

  def stdev(self, sumsquares, n, mean):
    if n == 0:
      return 0
    else:
      return (sumsquares / n) - (mean * mean)

  def summarize(self, feature_fpath, ntrials):
    # load data
    with open(feature_fpath, 'r') as f:
      reader = csv.DictReader(f, fieldnames=FIELDNAMES)
      for row in reader:
        # add to data
        try:
          for k,v in row.items():
            self._data[k] += int(v)
        except ValueError:
          continue
        # determine winner and add to data for that winner's victories
        winner = int(row['winner'])
        if winner == -1:
          self._control_victories += 1
          for k,v in row.items():
            self._control_data[k] += int(v)
        elif winner == 1:
          self._test_victories += 1
          for k,v in row.items():
            self._test_data[k] += int(v)
    # calculate summary metrics
    self.summarize_duration(self._data, self._summary, ntrials)
    self.summarize_duration(self._control_data, self._control_summary, self._control_victories)
    self.summarize_duration(self._test_data, self._test_summary, self._test_victories)
    self.summarize_actions(self._data, self._summary, ntrials)
    self.summarize_actions(self._control_data, self._control_summary, self._control_victories)
    self.summarize_actions(self._test_data, self._test_summary, self._test_victories)
    self.summarize_damage(self._data, self._summary, ntrials)
    self.summarize_damage(self._control_data, self._control_summary, self._control_victories)
    self.summarize_damage(self._test_data, self._test_summary, self._test_victories)
    self.summarize_sw_remaining(self._data, self._summary, ntrials)
    self.summarize_sw_remaining(self._control_data, self._control_summary, self._control_victories)
    self.summarize_sw_remaining(self._test_data, self._test_summary, self._test_victories)
    # TODO: summarize AP
    self.summarize_vp(self._data, self._summary, ntrials)
    self.summarize_vp(self._control_data, self._control_summary, self._control_victories)
    self.summarize_vp(self._test_data, self._test_summary, self._test_victories)

  def summarize_actions(self, datad, summaryd, n):
    #
    # summarize actions taken
    summaryd['control_actions_taken_mean'] = self.mean(datad['control_actions_taken'], n)
    summaryd['test_actions_taken_mean'] = self.mean(datad['test_actions_taken'], n)
    #
    # summarize attacks taken
    summaryd['control_attacks_taken_mean'] = self.mean(datad['control_attacks_taken'], n)
    summaryd['test_attacks_taken_mean'] = self.mean(datad['test_attacks_taken'], n)
    #
    # summarize parries taken
    summaryd['control_parries_taken_mean'] = self.mean(datad['control_parries_taken'], n)
    summaryd['test_parries_taken_mean'] = self.mean(datad['test_parries_taken'], n)
    return

  def summarize_damage(self, datad, summaryd, n):
    #
    # summarize control group damage rolls
    control_damage_mean = self.mean(datad['control_damage_rolls_sum'], datad['control_damage_rolls_count'])
    summaryd['control_damage_mean'] = control_damage_mean
    control_damage_stdev = self.stdev(datad['control_damage_rolls_sumsquares'], datad['control_damage_rolls_count'], control_damage_mean)
    summaryd['control_damage_stdev'] = control_damage_stdev
    #
    # summarize test group damage rolls
    test_damage_mean = self.mean(datad['test_damage_rolls_sum'], datad['test_damage_rolls_count'])
    summaryd['test_damage_mean'] = test_damage_mean
    test_damage_stdev = self.stdev(datad['test_damage_rolls_sumsquares'], datad['test_damage_rolls_count'], test_damage_mean)
    summaryd['test_damage_stdev'] = test_damage_stdev
    #
    # TODO: summarize SW dealt
    #
    return

  def summarize_duration(self, datad, summaryd, n):
    #
    # summarize duration in rounds
    summaryd['duration_rounds_mean'] = self.mean(datad['duration_rounds'], n)
    #
    # summarize duration in phases
    summaryd['duration_phases_mean'] = self.mean(datad['duration_phases'], n)
    return

  def summarize_sw_remaining(self, datad, summaryd, n): 
    #
    # summarize sw remaining
    summaryd['test_sw_remaining_mean'] = self.mean(datad['test_sw_remaining'], n)
    summaryd['control_sw_remaining_mean'] = self.mean(datad['control_sw_remaining'], n)
    return 

  def summarize_vp(self, datad, summaryd, n):
    #
    # vp remaining
    summaryd['control_vp_remaining_mean'] = self.mean(datad['control_vp_remaining'], n)
    summaryd['test_vp_remaining_mean'] = self.mean(datad['test_vp_remaining'], n)
    #
    # vp spent
    summaryd['control_vp_spent_mean'] = self.mean(datad['control_vp_spent'], n)
    summaryd['test_vp_spent_mean'] = self.mean(datad['test_vp_spent'], n)
    #
    # vp spent on attack rolls
    summaryd['control_vp_spent_attacks_mean'] = self.mean(datad['control_vp_spent_attacks'], n)
    summaryd['test_vp_spent_attacks_mean'] = self.mean(datad['test_vp_spent_attacks'], n)
    #
    # vp spent on wound checks
    summaryd['control_vp_spent_wound_checks_mean'] = self.mean(datad['control_vp_spent_wound_checks'], n)
    summaryd['test_vp_spent_wound_checks_mean'] = self.mean(datad['test_vp_spent_wound_checks'], n)
    return

  def print_report(self):
    # duration summary
    print('Average combat duration in rounds: {}'.format(self._summary['duration_rounds_mean']))
    print('Average combat duration in phases: {}'.format(self._summary['duration_phases_mean']))
    print('')
    # test group stats
    print('Test group stats:')
    print('\tSW remaining mean: {}'.format(self._summary['test_sw_remaining_mean']))
    print('\tDamage roll mean: {}'.format(self._summary['test_damage_mean']))
    print('\tDamage roll stdev: {}'.format(self._summary['test_damage_stdev']))
    print('\tVP remaining mean: {}'.format(self._summary['test_vp_remaining_mean']))
    print('\tVP spent mean: {}'.format(self._summary['test_vp_spent_mean']))
    print('\tVP spent on attacks mean: {}'.format(self._summary['test_vp_spent_attacks_mean']))
    print('\tVP spent on wound checks mean: {}'.format(self._summary['test_vp_spent_wound_checks_mean']))
    print('\tActions taken mean: {}'.format(self._summary['test_actions_taken_mean']))
    print('\tAttacks taken mean: {}'.format(self._summary['test_attacks_taken_mean']))
    print('\tParries taken mean: {}'.format(self._summary['test_parries_taken_mean']))
    print('')
    # control group stats
    print('Control group stats:')
    print('\tSW remaining mean: {}'.format(self._summary['control_sw_remaining_mean']))
    print('\tDamage roll mean: {}'.format(self._summary['control_damage_mean']))
    print('\tDamage roll stdev: {}'.format(self._summary['control_damage_stdev']))
    print('\tVP remaining mean: {}'.format(self._summary['control_vp_remaining_mean']))
    print('\tVP spent mean: {}'.format(self._summary['control_vp_spent_mean']))
    print('\tVP spent on attacks mean: {}'.format(self._summary['control_vp_spent_attacks_mean']))
    print('\tVP spent on wound checks mean: {}'.format(self._summary['control_vp_spent_wound_checks_mean']))
    print('\tActions taken mean: {}'.format(self._summary['control_actions_taken_mean']))
    print('\tAttacks taken mean: {}'.format(self._summary['control_attacks_taken_mean']))
    print('\tParries taken mean: {}'.format(self._summary['control_parries_taken_mean']))
    if self._test_victories > 0:
      # stats given test group victory
      print('')
      print('Features given test group victory:')
      print('\tAverage combat duration in rounds: {}'.format(self._test_summary['duration_rounds_mean']))
      print('\tAverage combat duration in phases: {}'.format(self._test_summary['duration_phases_mean']))
      print('\t')
      print('\tTest group stats:')
      print('\t\tSW remaining mean: {}'.format(self._test_summary['test_sw_remaining_mean']))
      print('\t\tDamage roll mean: {}'.format(self._test_summary['test_damage_mean']))
      print('\t\tDamage roll stdev: {}'.format(self._test_summary['test_damage_stdev']))
      print('\t\tVP remaining mean: {}'.format(self._summary['test_vp_remaining_mean']))
      print('\t\tVP spent mean: {}'.format(self._test_summary['test_vp_spent_mean']))
      print('\t\tVP spent on attacks mean: {}'.format(self._test_summary['test_vp_spent_attacks_mean']))
      print('\t\tVP spent on wound checks mean: {}'.format(self._test_summary['test_vp_spent_wound_checks_mean']))
      print('\t\tActions taken mean: {}'.format(self._test_summary['test_actions_taken_mean']))
      print('\t\tAttacks taken mean: {}'.format(self._test_summary['test_attacks_taken_mean']))
      print('\t\tParries taken mean: {}'.format(self._test_summary['test_parries_taken_mean']))
      print('\t')
      print('\tControl group stats:')
      print('\t\tSW remaining mean: {}'.format(self._test_summary['control_sw_remaining_mean']))
      print('\t\tDamage roll mean: {}'.format(self._test_summary['control_damage_mean']))
      print('\t\tDamage roll stdev: {}'.format(self._test_summary['control_damage_stdev']))
      print('\t\tVP remaining mean: {}'.format(self._summary['control_vp_remaining_mean']))
      print('\t\tVP spent mean: {}'.format(self._test_summary['control_vp_spent_mean']))
      print('\t\tVP spent on attacks mean: {}'.format(self._test_summary['control_vp_spent_attacks_mean']))
      print('\t\tVP spent on wound checks mean: {}'.format(self._test_summary['control_vp_spent_wound_checks_mean']))
      print('\t\tActions taken mean: {}'.format(self._test_summary['control_actions_taken_mean']))
      print('\t\tAttacks taken mean: {}'.format(self._test_summary['control_attacks_taken_mean']))
      print('\t\tParries taken mean: {}'.format(self._test_summary['control_parries_taken_mean']))
    if self._control_victories > 0:
      # stats given control group victory 
      print('')
      print('Features given control group victory:')
      print('\tAverage combat duration in rounds: {}'.format(self._control_summary['duration_rounds_mean']))
      print('\tAverage combat duration in phases: {}'.format(self._control_summary['duration_phases_mean']))
      print('\t')
      print('\tTest group stats:')
      print('\t\tSW remaining mean: {}'.format(self._control_summary['test_sw_remaining_mean']))
      print('\t\tDamage roll mean: {}'.format(self._control_summary['test_damage_mean']))
      print('\t\tDamage roll stdev: {}'.format(self._control_summary['test_damage_stdev']))
      print('\t\tVP remaining mean: {}'.format(self._summary['test_vp_remaining_mean']))
      print('\t\tVP spent mean: {}'.format(self._control_summary['test_vp_spent_mean']))
      print('\t\tVP spent on attacks mean: {}'.format(self._control_summary['test_vp_spent_attacks_mean']))
      print('\t\tVP spent on wound checks mean: {}'.format(self._control_summary['test_vp_spent_wound_checks_mean']))
      print('\t\tActions taken mean: {}'.format(self._control_summary['test_actions_taken_mean']))
      print('\t\tAttacks taken mean: {}'.format(self._control_summary['test_attacks_taken_mean']))
      print('\t\tParries taken mean: {}'.format(self._control_summary['test_parries_taken_mean']))
      print('\t')
      print('\tControl group stats:')
      print('\t\tSW remaining mean: {}'.format(self._control_summary['control_sw_remaining_mean']))
      print('\t\tDamage roll mean: {}'.format(self._control_summary['control_damage_mean']))
      print('\t\tDamage roll stdev: {}'.format(self._control_summary['control_damage_stdev']))
      print('\t\tVP remaining mean: {}'.format(self._summary['control_vp_remaining_mean']))
      print('\t\tVP spent mean: {}'.format(self._control_summary['control_vp_spent_mean']))
      print('\t\tVP spent on attacks mean: {}'.format(self._control_summary['control_vp_spent_attacks_mean']))
      print('\t\tVP spent on wound checks mean: {}'.format(self._control_summary['control_vp_spent_wound_checks_mean']))
      print('\t\tActions taken mean: {}'.format(self._control_summary['control_actions_taken_mean']))
      print('\t\tAttacks taken mean: {}'.format(self._control_summary['control_attacks_taken_mean']))
      print('\t\tParries taken mean: {}'.format(self._test_summary['control_parries_taken_mean']))
    return


class TrialFeatures(object):
  '''
  Features of a single run.
  '''
  def __init__(self):
    self._data = {}
    self._winner = 0
    self.initialize()

  def clear(self):
    self.initialize()

  def data(self):
    return self._data

  def winner(self):
    return self._winner

  def initialize(self):
    '''
  Questions we might ask after a simulation:
  * Winner's normal initiative actions per round compared to loser
  * Winner's total SW compared to loser (at beginning of combat)
  * Interrupt actions taken
  * Interrupt attacks taken
  * Interrupt parries taken
  '''
    # winner (-1: control, 0: aiuchi, 1: test)
    self._winner = 0
    # duration of trial
    self._data['duration_rounds'] = 0
    self._data['duration_phases'] = 0
    # control's actions
    self._data['control_actions_taken'] = 0
    self._data['control_attacks_taken'] = 0
    self._data['control_parries_taken'] = 0
    # control's AP
    self._data['control_ap_remaining'] = 0
    self._data['control_ap_spent'] = 0
    self._data['control_ap_spent_wound_checks'] = 0
    # control's damage inflicted
    self._data['control_damage_rolls'] = []
    self._data['control_sw'] = 0
    # control's SW remaining
    self._data['control_sw_remaining'] = 0
    # control's VP
    self._data['control_vp_remaining'] = 0
    self._data['control_vp_spent'] = 0
    self._data['control_vp_spent_attacks'] = 0
    self._data['control_vp_spent_wound_checks'] = 0
    # test's actions
    self._data['test_actions_taken'] = 0
    self._data['test_attacks_taken'] = 0
    self._data['test_parries_taken'] = 0
    # test's AP
    self._data['test_ap_remaining'] = 0
    self._data['test_ap_spent'] = 0
    self._data['test_ap_spent_wound_checks'] = 0
    # test's damage inflicted
    self._data['test_damage_rolls'] = []
    self._data['test_sw'] = 0
    # test's SW remaining
    self._data['test_sw_remaining'] = 0
    # test's VP
    self._data['test_vp_remaining'] = 0
    self._data['test_vp_spent'] = 0
    self._data['test_vp_spent_attacks'] = 0
    self._data['test_vp_spent_wound_checks'] = 0

  def observe_event(self, event, context):
    if isinstance(event, events.NewPhaseEvent):
      self.observe_phase()
    elif isinstance(event, events.NewRoundEvent):
      self.observe_round()
    elif isinstance(event, events.LightWoundsDamageEvent):
      self.observe_lw(event, context)
    elif isinstance(event, events.SeriousWoundsDamageEvent):
      self.observe_sw(event, context)
    elif isinstance(event, events.SpendActionEvent):
      self.observe_action(event, context)
    elif isinstance(event, events.SpendAdventurePointsEvent):
      raise NotImplementedError('Collecting features for spend_ap events is not yet supported')
    elif isinstance(event, events.SpendVoidPointsEvent):
      self.observe_vp_spent(event, context)
    elif isinstance(event, events.TakeAttackActionEvent):
      self.observe_attack(event, context)
    elif isinstance(event, events.TakeParryActionEvent):
      self.observe_parry(event, context)
    elif isinstance(event, events.AttackSucceededEvent):
      # TODO: collect successful attacks
      pass
    elif isinstance(event, events.AttackFailedEvent):
      # TODO: collect failed attacks
      pass
    elif isinstance(event, events.ParrySucceededEvent):
      # TODO: collect successful parries
      pass
    elif isinstance(event, events.WoundCheckSucceededEvent):
      # TODO: collect successful wound checks
      pass
    elif isinstance(event, events.WoundCheckFailedEvent):
      # TODO: collect failed wound checks and LW total at the time
      pass
    elif isinstance(event, events.TakeSeriousWoundEvent):
      # TODO: collect number of times character took SW after successful wound check
      # and what the LW total was at the time
      pass

  def observe_action(self, event, context):
    if event.subject in context.test_group():
      self._data['test_actions_taken'] += 1
    else:
      self._data['control_actions_taken'] += 1

  def observe_attack(self, event, context):
    if event.action.subject() in context.test_group():
      self._data['test_attacks_taken'] += 1
    else:
      self._data['control_attacks_taken'] += 1

  def observe_lw(self, event, context):
    if event.subject in context.test_group():
      self._data['test_damage_rolls'].append(event.damage)
    else:
      self._data['control_damage_rolls'].append(event.damage)

  def observe_parry(self, event, context):
    if event.action.subject() in context.test_group():
      self._data['test_parries_taken'] += 1
    else:
      self._data['control_parries_taken'] += 1

  def observe_phase(self):
    self._data['duration_phases'] += 1

  def observe_round(self):
    self._data['duration_rounds'] += 1

  def observe_sw(self, event, context):
    if event.subject in context.test_group():
      self._data['test_sw'] += event.damage
    else:
      self._data['control_sw'] += event.damage

  def observe_vp_spent(self, event, context):
    if event.subject in context.test_group():
      self._data['test_vp_spent'] += 1
      if event.skill in ATTACK_SKILLS:
        self._data['test_vp_spent_attacks'] += 1
      elif event.skill == 'wound check':
        self._data['test_vp_spent_wound_checks'] += 1
    else:
      self._data['control_vp_spent'] += 1
      if event.skill in ATTACK_SKILLS:
        self._data['control_vp_spent_attacks'] += 1
      elif event.skill == 'wound check':
        self._data['control_vp_spent_wound_checks'] += 1

  def observe_winner(self, result):
    '''
    observe_winner(result)

    Set the winner of this simulation.
    -1 = control group won
    0 = both sides lost
    1 = test group won
    '''
    self._winner = result
    self._data['winner'] = result

  def complete(self, context):
    self.complete_damage_rolls(context)
    self.complete_sw_remaining(context)
    self.complete_vp_remaining(context)
 
  def complete_damage_rolls(self, context):
    # get count, sum, and sum of squares for control damage rolls
    control_damage = self._data['control_damage_rolls']
    self._data['control_damage_rolls_sum'] = sum(control_damage)
    self._data['control_damage_rolls_sumsquares'] = sum([x * x for x in control_damage])
    self._data['control_damage_rolls_count'] = len(control_damage)
    self._data.pop('control_damage_rolls')
    # get count, sum, and sum of squares for test damage rolls
    test_damage = self._data['test_damage_rolls']
    self._data['test_damage_rolls_sum'] = sum(test_damage)
    self._data['test_damage_rolls_sumsquares'] = sum([x * x for x in test_damage])
    self._data['test_damage_rolls_count'] = len(test_damage)
    self._data.pop('test_damage_rolls')

  def complete_sw_remaining(self, context):
    control_sw_remaining = sum([character.sw_remaining() for character in context.groups()[0]])
    test_sw_remaining = sum([character.sw_remaining() for character in context.groups()[1]])
    self._data['control_sw_remaining'] = control_sw_remaining
    self._data['test_sw_remaining'] = test_sw_remaining

  def complete_vp_remaining(self, context):
    control_vp_remaining = sum([character.vp() for character in context.groups()[0]])
    test_vp_remaining = sum([character.vp() for character in context.groups()[1]])
    self._data['control_vp_remaining'] = control_vp_remaining
    self._data['test_vp_remaining'] = test_vp_remaining

  def write(self, f):
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writerow(self._data)

def write_feature_file_header(f):
  writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
  writer.writeheader()

