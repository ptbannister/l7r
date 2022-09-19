
from simulation.attack_engine import AttackEngine


class Action(object):
  def __init__(self, subject, target, ring, skill):
    self._subject = subject
    self._target = target
    self._ring = ring
    self._skill = skill

  def ring(self):
    return self._ring

  def skill(self):
    return self._skill

  def subject(self):
    return self._subject

  def target(self):
    return self._target


class AttackAction(Action):
  def __init__(self, subject, target, weapon_rolled=4, weapon_kept=2, roll_provider=None):
    super().__init__(subject, target, 'fire', 'attack')
    self._attack_roll = None
    self._damage_roll = None
    self._parries_declared = []
    self._parried = False
    self._weapon_rolled = weapon_rolled
    self._weapon_kept = weapon_kept

  def add_parry_declared(self, event):
    self._parries_declared.append(event)

  def calculate_extra_damage_dice(self):
    return (self._attack_roll - self.tn()) // 5

  def is_hit(self):
    tn = self._target.base_to_hit_tn()
    return self._attack_roll >= tn and not self._parried

  def parried(self):
    return self._parried

  def parries_declared(self):
    return self._parries_declared

  def roll_attack(self):
    self._attack_roll = self._subject.roll_skill(self.ring(), self.skill())
    return self._attack_roll

  def roll_damage(self):
    extra_rolled = self.calculate_extra_damage_dice()
    self._damage_roll = self._subject.roll_damage(self.skill(), extra_rolled, self._weapon_rolled, self._weapon_kept)
    return self._damage_roll

  def run(self, context):
    AttackEngine(context, self).run()

  def tn(self):
    return self._target.base_to_hit_tn() 


class ParryAction(Action):
  def __init__(self, subject, target, attack):
    super().__init__(subject, target, 'air', 'parry')
    self._attack = attack

