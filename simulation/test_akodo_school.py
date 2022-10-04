#!/usr/bin/env python3

#
# test_akodo_school.py
#
# Unit tests for the Akodo Bushi School.
#

import logging
import sys
import unittest

from simulation import actions, akodo_school, events
from simulation.character import Character
from simulation.context import EngineContext
from simulation.groups import Group
from simulation.log import logger
 
# set up logging
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class TestAkodoAttackFailedListener(unittest.TestCase):
  def test_feint_failed(self):
    akodo = Character('Akodo')
    bayushi = Character('Bayushi')
    context = EngineContext([Group([akodo]), Group([bayushi])])
    action = actions.FeintAction(akodo, bayushi)
    event = events.AttackFailedEvent(action)
    listener = akodo_school.AkodoAttackFailedListener()
    responses = list(listener.handle(akodo, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.GainTemporaryVoidPointsEvent))
    self.assertEqual(akodo, response.subject)
    self.assertEqual(1, response.amount)

class TestAkodoAttackSucceededListener(unittest.TestCase):
  def test_feint_succeeded(self):
    akodo = Character('Akodo')
    bayushi = Character('Bayushi')
    context = EngineContext([Group([akodo]), Group([bayushi])])
    action = actions.FeintAction(akodo, bayushi)
    event = events.AttackSucceededEvent(action)
    listener = akodo_school.AkodoAttackSucceededListener()
    responses = list(listener.handle(akodo, event, context))
    self.assertEqual(1, len(responses))
    response = responses[0]
    self.assertTrue(isinstance(response, events.GainTemporaryVoidPointsEvent))
    self.assertEqual(akodo, response.subject)
    self.assertEqual(4, response.amount)

class TestAkodoFifthDanStrategy(unittest.TestCase):
  def test_inflict_lw(self):
    akodo = Character('Akodo')
    bayushi = Character('Bayushi')
    context = EngineContext([Group([akodo]), Group([bayushi])])
    event = events.LightWoundsDamageEvent(bayushi, akodo, 7)
    strategy = akodo_school.AkodoFifthDanStrategy()
    responses = list(strategy.recommend(akodo, event, context))
    self.assertEqual(2, len(responses))
    first_event = responses[0]
    self.assertTrue(isinstance(first_event, events.SpendVoidPointsEvent))
    self.assertEqual(akodo, first_event.subject)
    self.assertEqual(2, first_event.amount)
    second_event = responses[1]
    self.assertTrue(isinstance(second_event, events.LightWoundsDamageEvent))
    self.assertEqual(akodo, second_event.subject)
    self.assertEqual(bayushi, second_event.target)
    self.assertEqual(20, second_event.damage)

  def test_no_vp(self):
    akodo = Character('Akodo')
    bayushi = Character('Bayushi')
    context = EngineContext([Group([akodo]), Group([bayushi])])
    akodo.spend_vp(2)
    bayushi = Character('Bayushi')
    event = events.LightWoundsDamageEvent(bayushi, akodo, 7)
    strategy = akodo_school.AkodoFifthDanStrategy()
    responses = list(strategy.recommend(akodo, event, context))
    self.assertEqual([], responses)

