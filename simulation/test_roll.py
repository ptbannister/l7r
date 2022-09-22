#!/usr/bin/env python3

#
# test_roll.py
# Author: Patrick Bannister
# Unit tests for L7R combat simulator roll module
#

import unittest

from simulation.roll import InitiativeRoll, Roll, TestDice, normalize_roll_params

class TestNormalize(unittest.TestCase):
  def test_normal(self):
    self.assertEqual((1, 1, 0), normalize_roll_params(1, 1))
    self.assertEqual((6, 3, 0), normalize_roll_params(6, 3))
    self.assertEqual((10, 10, 0), normalize_roll_params(10, 10))
    self.assertEqual((7, 3, 0), normalize_roll_params(7, 3))

  def test_excess_rolled(self):
    self.assertEqual((10, 5, 0), normalize_roll_params(12, 3))
    self.assertEqual((10, 5, 0), normalize_roll_params(11, 4))
    self.assertEqual((10, 10, 0), normalize_roll_params(14, 6))

  def test_excess_kept(self):
    self.assertEqual((10, 10, 1), normalize_roll_params(11, 10))
    self.assertEqual((10, 10, 5), normalize_roll_params(17, 8))
    self.assertEqual((10, 10, 10), normalize_roll_params(25, 5))

  def test_bonus(self):
    self.assertEqual((6, 3, 5), normalize_roll_params(6, 3, 5))
    self.assertEqual((7, 3, 5), normalize_roll_params(7, 3, 5))
    self.assertEqual((10, 10, 6), normalize_roll_params(15, 6, 5))


class TestInitiativeRoll(unittest.TestCase):
  def test_keep_low(self):
    test_dice = TestDice()
    test_dice.extend([11, 9, 1, 1])
    roll = InitiativeRoll(4, 3, die_source=test_dice)
    self.assertEqual([1, 1, 9], roll.roll())


class TestRoll(unittest.TestCase):
  def test_roll_ones(self):
    # roll 5k1 on one-sided dice without exploding
    roll = Roll(5, 1, faces=1, explode=False)
    # result should be 1 with no bonus
    self.assertTrue(roll.roll() == 1)

  def test_roll(self):
    test_dice = TestDice()
    test_dice.extend([1, 1, 3, 5, 7, 9])
    roll = Roll(6, 3, die_source=test_dice)
    self.assertEqual(21, roll.roll())

  def test_excess_rolled(self):
    test_dice = TestDice()
    test_dice.extend([1, 2, 3, 4, 5, 6, 7, 8, 9, 11])
    roll = Roll(12, 2, die_source=test_dice)
    self.assertEqual(35, roll.roll())

  def test_excess_kept(self):
    test_dice = TestDice()
    test_dice.extend([1, 2, 3, 4, 5, 6, 7, 8, 9, 11])
    roll = Roll(15, 10, die_source=test_dice)
    self.assertEqual(61, roll.roll())


class TestTestDice(unittest.TestCase):
  def test_empty(self):
    with self.assertRaises(IndexError):
      TestDice().roll_die()

  def test_fifo(self):
    test_dice = TestDice()
    test_dice.append(1)
    test_dice.append(2)
    test_dice.append(3)
    self.assertEqual(1, test_dice.roll_die())
    self.assertEqual(2, test_dice.roll_die())
    self.assertEqual(3, test_dice.roll_die())

  def test_extend(self):
    test_dice = TestDice()
    results = [3, 2, 1]
    test_dice.extend(results)
    self.assertEqual(3, test_dice.roll_die())
    self.assertEqual(2, test_dice.roll_die())
    self.assertEqual(1, test_dice.roll_die())


if (__name__ == '__main__'):
  unittest.main()

