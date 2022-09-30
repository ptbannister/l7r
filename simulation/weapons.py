
from abc import ABC, abstractmethod

class Weapon(object):
  def __init__(self, name, rolled, kept):
    self._name = name
    self._rolled = rolled
    self._kept = kept

  def name(self):
    return self._name

  def kept(self):
    return self._kept

  def rolled(self):
    return self._rolled


KATANA = Weapon('katana', 4, 2)

UNARMED = Weapon('unarmed', 0, 2)

GONGFU = Weapon('gongfu', 0, 3)

