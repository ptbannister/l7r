
import unittest
from simulation.character import Character
from simulation.context import EngineContext
from simulation.events import AttackDeclaredEvent, AttackRolledEvent, AttackSucceededEvent, DeathEvent, LightWoundsDamageEvent, UnconsciousEvent
from simulation.exceptions import CombatEnded


class TestEngineContext(unittest.TestCase):
  def test_death_combat_continues(self):
    akodo = Character('Akodo')
    bayushi = Character('Bayushi')
    chiba = Character('Chiba')
    doji = Character('Doji')
    context = EngineContext([[akodo, bayushi], [chiba, doji]])
    # chiba dies
    chiba.take_sw(5)
    event = DeathEvent(chiba)
    # doji is still fighting, combat should continue
    try:
      context.update_status(event)
    except:
      self.fail('Combat should continue when only one character dies!')

  def test_death_combat_ends_death(self):
    akodo = Character('Akodo')
    bayushi = Character('Bayushi')
    chiba = Character('Chiba')
    doji = Character('Doji')
    context = EngineContext([[akodo, bayushi], [chiba, doji]])
    # akodo and bayushi both die
    akodo.take_sw(5)
    bayushi.take_sw(5)
    event = DeathEvent(bayushi)
    # combat should end
    with self.assertRaises(CombatEnded):
      context.update_status(event)
 
  def test_combat_ends_unconsciousness(self):
    akodo = Character('Akodo')
    bayushi = Character('Bayushi')
    chiba = Character('Chiba')
    doji = Character('Doji')
    context = EngineContext([[akodo, bayushi], [chiba, doji]])
    # akodo and bayushi both die
    akodo.take_sw(5)
    bayushi.take_sw(4)
    event = UnconsciousEvent(bayushi)
    # combat should end
    with self.assertRaises(CombatEnded):
      context.update_status(event)

  def test_load_probability(self):
    context = EngineContext([[Character(),], [Character(),]])
    context.load_probability_data()
    # P(1) on 1k1 should be 1.0
    self.assertEqual(1.00, context.p(1, 1, 1))
    # P(10) on 10k10 should be 1.0
    self.assertEqual(1.00, context.p(10, 10, 10))
     
