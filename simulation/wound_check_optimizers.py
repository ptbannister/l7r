#!/usr/bin/env python3

#
# wound_check_optimizers.py
#
# Classes to optimize resources spent on wound checks.
#

from abc import ABC, abstractmethod

from simulation.events import LightWoundsDamageEvent, WoundCheckDeclaredEvent, WoundCheckRolledEvent
from simulation.knowledge import TheoreticalCharacter
from simulation.log import logger


class ProbabilityForResources(object):
  '''
  Container class to hold the probability of meeting the target number
  given an expenditure of vp and ap.
  '''
  def __init__(self, p, vp, ap):
    self.p = p
    self.vp = vp
    self.ap = ap

  def sort_key_by_cost(self):
    '''
    sort_by_cost() -> int

    Returns a number that values VP more than AP, but spends an extra VP before spending 4 or 5 AP.
    '''
    vp_value = 4 * self.vp if self.ap < 4 else (6 * (self.vp + 1)) - 2
    ap_value = self.ap if self.ap <= 3 else self.ap + 4
    return vp_value + ap_value


class WoundCheckOptimizer(ABC):
  '''
  Class that helps optimize spending resources on a wound check roll
  by calculating the probability of success when spending different
  amounts of VP and other available resources.
  '''
  @abstractmethod
  def declare(self, max_sw, threshold):
    ''''
    declare(max_sw, threshold) -> DeclareWoundCheckEvent
      max_sw (int): maximum SW the subject can tolerate
      threshold (float): probability of success desired

    Returns a WoundCheckDeclaredEvent that will spend the number
    of VP required to take the tolerable number of SW at the
    desired threshold for probability of success.
    '''
    pass


class DefaultWoundCheckOptimizer(object):
  '''
  Class that helps optimize spending resources on a wound check roll
  by calculating the probability of success when spending different
  amounts of VP and other available resources.
  '''
  def __init__(self, subject, event, context, max_vp=None, max_ap=None):
    '''
    __init__(subject, max_vp=None)
      subject (Character): character who is making the wound check
      event (Event): LightWoundsDamageEvent that led to this wound check
      context (EngineContext): context
      max_vp (int): maximum VP the character will spend. If None,
        will spend the maximum possible to improve the wound check.
      max_ap (int): maximum AP the character will spend. If None,
        will spend the maximum possible to improve the wound check.
    '''
    self.subject = subject
    self.event = event
    self.context = context
    self.max_vp = max_vp
    self.max_ap = max_ap
    self.original_max_vp = max_vp
    self.original_max_ap = max_ap
    self.sw_to_roll = {}
    self.p_for_resources = []
    self.initialize()
  
  def initialize(self):
    # reset state
    self.sw_to_roll.clear()
    self.p_for_resources.clear()
    # determine max vp that may be spent on this roll
    self.max_vp = self.original_max_vp
    if self.max_vp is None:
      # if no limit set: maximum is character's maximum allowed VP expenditure
      self.max_vp = min(self.subject.max_vp_per_roll(), self.subject.vp())
    # determine max ap that may be spent on this roll
    self.max_ap = self.original_max_ap
    if self.max_ap is None:
      self.max_ap = min(self.subject.max_ap_per_roll(), self.subject.ap())
    # find the break points where the character takes fewer SW
    sw = 100
    prev_sw = sw
    roll = 0
    while sw > 0:
      sw = self.subject.wound_check(roll)
      if sw < prev_sw:
        self.sw_to_roll[sw] = roll
        prev_sw = sw
      if sw == 0:
        break
      roll += 1

  def declare(self, max_sw, threshold):
    '''
    declare(character, event, max_sw, theshold, context) -> WoundCheckDeclaredEvent
      character (Character): character who is making the wound check

    Returns a WoundCheckDeclaredEvent to spend VP for an acceptable
    level of risk on a wound check.
    '''
    # plan to use any available floating bonuses
    bonus = sum([b.bonus() for b in self.subject.floating_bonuses('wound check')])
    # get tn for desired SW
    if max_sw not in self.sw_to_roll.keys():
      # if the sw_to_roll mapping doesn't contain max_sw,
      # then there is no risk of taking max_sw and no resources should be used
      return WoundCheckDeclaredEvent(self.subject, self.event.subject, self.event.damage, 0)
    tn = self.sw_to_roll[max_sw] - bonus
    # calculate probability of reaching this tn for various resource expenditures
    for vp in range(self.max_vp + 1):
      (rolled, kept, mod) = self.subject.get_wound_check_roll_params(vp)
      for ap in range(self.max_ap + 1):
        adjusted_tn = tn - (5 * ap) - mod
        p_tn = self.context.p(adjusted_tn, rolled, kept)
        self.p_for_resources.append(ProbabilityForResources(p_tn, vp, ap))
      if kept == 10:
        # do not spend additional vp after keeping 10 dice
        break
    # sort results by cost
    self.p_for_resources.sort(key=lambda x: x.sort_key_by_cost())
    # iterate through results until the first one is found that satisfies the threshold
    (vp, ap) = (0, 0)
    for result in self.p_for_resources:
      if result.p >= threshold:
        (vp, ap) = (result.vp, result.ap)
        logger.debug('{} declaring wound check with {} vp (planning to spend {} ap) to take {} SW with probability {}' \
          .format(self.subject.name(), vp, ap, max_sw, result.p))
        break
    return WoundCheckDeclaredEvent(self.subject, self.event.subject, self.event.damage, vp)


class KeepLightWoundsOptimizer(ABC):
  '''
  Class that helps make decisions about keeping Light Wounds after
  a successful Wound Check.
  '''
  @abstractmethod
  def should_keep(self, max_sw, threshold):
    '''
    keep(max_sw, threshold) -> bool
      max_sw (int): maximum number of SW this character is willing to risk
      threshold (float): minimum probability desired of taking no more
        than the given max_sw.

    Returns whether this character should keep their current LW
    or take a Serious Wound instead.
    '''
    pass


class DefaultKeepLightWoundsOptimizer(KeepLightWoundsOptimizer):
  def __init__(self, subject, context):
    self.subject = subject
    self.context = context

  def should_keep(self, max_sw, threshold):
    # how much damage do we expect to take in the future?
    # TODO: revisit whether this is a good prediction of
    # future damage
    expected_damage = 0
    if len(self.subject.lw_history()) == 0:
      expected_damage = self.context.mean_roll(7, 2)
    else:
      expected_damage = int(sum(self.subject.lw_history()) / len(self.subject.lw_history()))
    future_damage = self.subject.lw() + expected_damage
    # what TN is needed to take no more than max_sw?
    sw = 100
    prev_sw = sw
    roll = 0
    sw_to_roll = {}
    while sw > 0:
      sw = self.subject.wound_check(roll, lw=future_damage)
      if sw < prev_sw:
        sw_to_roll[sw] = roll
        prev_sw = sw
      if sw == 0:
        break
      roll += 1
    if max_sw not in sw_to_roll.keys():
      # if max_sw isn't in the sw_to_roll dictionary,
      # then we should be safe to keep
      return True
    tn = sw_to_roll[max_sw]
    # plan to use any available floating bonuses
    bonus = sum([b.bonus() for b in self.subject.floating_bonuses('wound check')])
    tn -= bonus
    # what is the probability of making the TN?
    (rolled, kept, modifier) = self.subject.get_wound_check_roll_params()
    p_tn = self.context.p(tn - modifier, rolled, kept)
    return p_tn >= threshold

