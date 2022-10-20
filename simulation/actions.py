#!/usr/bin/env python3

#
# actions.py
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
    self._skill_roll = None

  def set_skill_roll(self, skill_roll):
    self._skill_roll = skill_roll

  def skill_roll(self):
    return self._skill_roll

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
      skill_roll = self.skill_roll()
    if tn is None:
      tn = self.tn()
    if self.parry_attempted():
      return 0
    else:
      return (skill_roll - self.tn()) // 5

  def damage_roll(self):
    return self._damage_roll

  def direct_damage(self):
    return None

  def is_hit(self):
    return self.skill_roll() >= self.tn() and not self.parried()

  def parried(self):
    return self._parried

  def parry_attempted(self):
    return self._parry_attempted

  def parries_declared(self):
    return self._parries_declared

  def parries_declined(self):
    return self._parries_declined

  def parries_predeclared(self):
    return self._parries_predeclared

  def parry_tn(self):
    return self.skill_roll()

  def roll_attack(self):
    self.set_skill_roll(self.subject().roll_skill(self.target(), self.skill(), self.vp()))
    return self.skill_roll()

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


class CounterattackAction(AttackAction):
  def __init__(self, subject, target, attack, vp=0):
    super().__init__(subject, target, 'counterattack', vp)
    self._original_attack = attack

  def attack(self):
    return self._original_attack

  def tn(self):
    penalty = 0 if self.attack().target() == self.subject() else 5 * self.attack().subject().skill('attack')
    return self.target().tn_to_hit() + penalty 
    


class DoubleAttackAction(AttackAction):
  def __init__(self, subject, target, vp=0):
    super().__init__(subject, target, 'double attack', vp)

  def calculate_extra_damage_dice(self, skill_roll=None, tn=None):
    if skill_roll is None:
      skill_roll = self.skill_roll()
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
    return SeriousWoundsDamageEvent(self.subject(), self.target(), 1)

  def tn(self):
    return self.target().tn_to_hit() + 20


class FeintAction(AttackAction):
  def __init__(self, subject, target, vp=0):
    super().__init__(subject, target, skill='feint', vp=vp)

  def calculate_extra_damage_dice(self, skill_roll=None, tn=None):
    return 0

  def roll_damage(self):
    return 0


class LungeAction(AttackAction):
  def __init__(self, subject, target, vp=0):
    super().__init__(subject, target, 'lunge', vp)

  def calculate_extra_damage_dice(self, skill_roll=None, tn=None):
    return super().calculate_extra_damage_dice(skill_roll, tn) + 1


class ParryAction(Action):
  def __init__(self, subject, target, attack, predeclared=False, vp=0):
    super().__init__(subject, target, 'parry', vp)
    self._attack = attack
    self._predeclared = predeclared

  def attack(self):
    return self._attack

  def is_success(self):
    return self.skill_roll() >= self.tn()

  def roll_parry(self):
    penalty = 0
    if self._attack.target() != self.subject():
      # parry on behalf of others has a penalty
      penalty = 10
    # roll parry
    self.set_skill_roll(self.subject().roll_skill(self.target(), self.skill(), self.vp()) - penalty)
    return self.skill_roll()

  def set_attack_parry_declared(self, event):
    self._attack.add_parry_declared(event)

  def set_attack_parried(self):
    self._attack.set_parried()

  def set_attack_parry_attempted(self):
    self._attack.set_parry_attempted()

  def tn(self):
    return self._attack.parry_tn()

