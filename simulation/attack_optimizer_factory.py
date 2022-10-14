#!/usr/bin/env python3

#
# attack_optimizer_factory.py
#
# Factory class to provide AttackOptimizer instances.
#

from abc import ABC, abstractmethod

from simulation.attack_optimizers import AttackOptimizer, DamageOptimizer


class AttackOptimizerFactory(ABC):
  @abstractmethod
  def get_optimizer(self, character, target, skill, context):
    pass


class DefaultAttackOptimizerFactory(object):
  def get_optimizer(self, character, target, skill, context):
    if skill == 'feint':
      return AttackOptimizer(character, target, skill, context)
    else:
      return DamageOptimizer(character, target, skill, context)

DEFAULT_ATTACK_OPTIMIZER_FACTORY = DefaultAttackOptimizerFactory()

