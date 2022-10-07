#!/usr/bin/env python3

#
# character_file.py
# Author: Patrick Bannister (ptbannister@gmail.com)
#
# Character file format for L7R combat simulator.
# Characters may be represented as a YAML file.
# YAML was selected because it is very human readable and human writable.
# If you wanted ASN.1 or XML instead, I'm not sorry.
#

import os
import yaml

from simulation.advantages import Advantage
from simulation.character import Character
from simulation.character_builder import CharacterBuilder
from simulation.disadvantages import Disadvantage
from simulation.professions import Profession
from simulation.school_factory import get_school
from simulation.skills import Skill


class CharacterReader(object):
  def read(self, f):
    data = yaml.safe_load(f)
    xp = int(data.get('xp', 100))
    builder = CharacterBuilder().with_xp(xp)
    if 'name' in data.keys():
      builder.with_name(data['name']) 
    # take profession or school
    if 'school' in data.keys():
      school = get_school(data['school'])
      builder = builder.with_school(school)
    elif 'profession' in data.keys():
      builder = builder.with_profession(data['profession'])
    else:
      raise IOError('Invalid Character (no profession or school)')
    # take disadvantages
    if 'disadvantages' in data.keys():
      for disadvantage in data['disadvantages']:
        builder.take_disadvantage('disadvantage')
    # buy advantages
    if 'advantages' in data.keys():
      for advantage in data['advantages']:
        builder.take_advantage('advantage')
    # character must have skills
    if 'skills' not in data.keys():
      raise IOError('Invalid Character (no skills)')
    # buy attack skill before other skills
    # this avoids getting ahead of parry
    if 'attack' in data['skills'].keys():
      rank = data['skills'].pop('attack')
      builder.buy_skill('attack', rank)
    # buy other skills
    for (skill, rank) in data['skills'].items():
      builder.buy_skill(skill, rank)
    # buy rings
    if 'rings' not in data.keys():
      raise IOError('Invalid Character (no rings)')
    for (ring, rank) in data['rings'].items():
      builder.buy_ring(ring, rank)
    return builder.build()


class CharacterWriter(object):
  def write(self, character, f):
    if character.profession():
      return ProfessionCharacterWriter().write(character, f)
    elif character.school():
      return SchoolCharacterWriter().write(character, f)
    else:
      return GenericCharacterWriter().write(character, f)


# TODO: handle Honor, Rank, and Recognition

class GenericCharacterWriter(CharacterWriter):
  def write(self, character, f):
    yaml.dump(self.build_data(character), f)

  def build_data(self, character):
    data = { 'rings': {}, 'skills': {}, 'advantages': [], 'disadvantages': [] }
    data['name'] = character.name()
    for (ring, rank) in character.rings().items():
      data['rings'][ring] = rank
    for (skill, rank) in character.skills().items():
      data['skills'][skill] = rank
    for advantage in character.advantages():
      data['advantages'].append(advantage)
    for disadvantage in character.disadvantages():
      data['disadvantages'].append(disadvantage)
    xp_cost = self.calculate_xp_cost(character)
    data['xp'] = xp_cost
    return data

  def calculate_ring_cost(self, character, ring, rank):
    if rank == 2:
      return 0
    elif rank > 5:
      raise ValueError('May not raise ring above 5')
    else:
      return sum([(5 * i) for i in range(3, rank + 1)])

  def calculate_skill_cost(self, character, skill, rank):
    return Skill(skill).get().cost(rank)

  def calculate_xp_cost(self, character):
    xp_cost = 0
    for (skill, rank) in character.skills().items():
      xp_cost += self.calculate_skill_cost(character, skill, rank)
    for (ring, rank) in character.rings().items():
      xp_cost += self.calculate_ring_cost(character, ring, rank)
    for advantage in character.advantages():
      xp_cost += Advantage(advantage).get().cost()
    for disadvantage in character.disadvantages():
      xp_cost += Disadvantage(disadvantage).get().cost()
    return xp_cost


class ProfessionCharacterWriter(GenericCharacterWriter):
  def build_data(self, character):
    data = super().build_data(character)
    data['profession'] = character.profession().name()
    return data


class SchoolCharacterWriter(GenericCharacterWriter):
  def build_data(self, character):
    data = super().build_data(character)
    data['school'] = character.school().name()
    return data

  def calculate_skill_cost(self, character, skill, rank):
    original_rank = 0
    if skill in ('attack', 'parry'):
      original_rank = 1
    elif skill in character.school().school_knacks():
      original_rank = 1
    return Skill(skill).get().cost(rank, original_rank)

  def calculate_ring_cost(self, character, ring, rank):
    original_rank = 2
    discount = 0
    if ring == character.school().school_ring():
      original_rank = 3
    else:
      if rank > 5:
        raise ValueError('May not raise {} above 5'.format(ring))
    if self.school_rank(character) >= 4 and ring == character.school().school_ring():
      original_rank = 4
      discount = 5
    return max(sum([(5 * i) - discount for i in range(original_rank + 1, rank + 1)]), 0)

  def school_rank(self, character):
    return min([character.skill(skill) for skill in character.school().school_knacks()])

