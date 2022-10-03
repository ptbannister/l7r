#!/usr/bin/env python3

#
# actions.py
# Author: Patrick Bannister (ptbannister@gmail.com)
#
# Classes for combat actions in the L7R combat simulator.
#

from simulation.events import SeriousWoundsDamageEvent


class Action(object):
  def __init__(self, subject, target, skill, vp=0):
    self._subject = subject
    self._target = target
    self._skill = skill
    self._vp = vp

  def skill(self):
    return self._skill

  def subject(self):
    return self._subject

  def target(self):
    return self._target

  def vp(self):
    return self._vp


class AttackAction(Action):
  def __init__(self, subject, target, skill='attack', vp=0):
    super().__init__(subject, target, skill, vp)
    self._attack_roll = None
    self._damage_roll = None
    self._parries_declared = []
    self._parries_declined = []
    self._parries_predeclared = []
    self._parried = False
    self._parry_attempted = False

  def add_parry_declared(self, event):
    self._parries_declared.append(event)

  def add_parry_predeclared(self, event):
    self._parries_predeclared.append(event)
    self.add_parry_declared(event)

  def add_parry_declined(self, character):
    self._parries_declined.append(character)

  def calculate_extra_damage_dice(self, skill_roll=None, tn=None):
    if skill_roll is None:
      skill_roll = self._attack_roll
    if tn is None:
      tn = self.tn()
    if self.parry_attempted():
      return 0
    else:
      return (skill_roll - self.tn()) // 5

  def direct_damage(self):
    return None

  def is_hit(self):
    return self._attack_roll >= self.tn() and not self.parried()

  def parried(self):
    return self._parried

  def parry_attempted(self):
    return self._parry_attempted

  def parries_declared(self):
    return self._parries_declared

  def parries_declined(self):
    return self._parries_declined

  def roll_attack(self):
    self._attack_roll = self.subject().roll_skill(self.target(), self.skill(), self.vp())
    self.subject().spend_vp(self.vp())
    return self._attack_roll

  def roll_damage(self):
    extra_rolled = self.calculate_extra_damage_dice()
    self._damage_roll = self.subject().roll_damage(self.target(), self.skill(), extra_rolled, self.vp())
    return self._damage_roll

  def set_parry_attempted(self):
    self._parry_attempted = True

  def set_parried(self):
    self._parried = True

  def tn(self):
    return self.target().tn_to_hit()


class DoubleAttackAction(AttackAction):
  def __init__(self, subject, target, vp=0):
    super().__init__(subject, target, 'double attack', vp)
    self._attack_roll = None
    self._damage_roll = None
    self._parries_declared = []
    self._parries_declined = []
    self._parries_predeclared = []
    self._parried = False
    self._parry_attempted = False

  def calculate_extra_damage_dice(self, skill_roll=None, tn=None):
    if skill_roll is None:
      skill_roll = self._attack_roll
    if tn is None:
      tn = self.tn() - 20
    penalty = 0
    if self.parry_attempted():
      for parry_event in self.parries_declared():
        if parry_event.action.subject() == self.target():
          # if the target attempts to parry,
          # double attack does 4 fewer dice of damage
          penalty = 4
          break
        else:
          # if a third character parries on behalf of the target,
          # double attack does 2 fewer dice of damage
          penalty = 2
    return ((skill_roll - self.tn()) // 5) - penalty

  def direct_damage(self):
    return SeriousWoundsDamageEvent(self.target(), 1)

  def tn(self):
    return self.target().tn_to_hit() + 20


class LungeAction(AttackAction):
  def __init__(self, subject, target, vp=0):
    super().__init__(subject, target, 'lunge', vp)

  def calculate_extra_damage_dice(self, skill_roll=None, tn=None):
    return super().calculate_extra_damage_dice(skill_roll, tn) + 1


class ParryAction(Action):
  def __init__(self, subject, target, attack, predeclared=False, vp=0):
    skill = 'parry'
    if (attack.target != subject):
      skill = 'parry_other'
    super().__init__(subject, target, skill, vp)
    self._attack = attack
    self._parry_roll = 0
    self._predeclared = predeclared

  def is_success(self):
    return self._parry_roll >= self._attack._attack_roll

  def roll_parry(self):
    penalty = 0
    if self._attack.target() != self.subject():
      # parry on behalf of others has a penalty
      penalty = 10
    # roll parry
    self._parry_roll = self.subject().roll_skill(self.target(), self.skill(), self.vp()) - penalty
    self.subject().spend_vp(self.vp())
    return self._parry_roll

  def set_attack_parry_declared(self, event):
    self._attack.add_parry_declared(event)

  def set_attack_parried(self):
    self._attack.set_parried()

  def set_attack_parry_attempted(self):
    self._attack.set_parry_attempted()

