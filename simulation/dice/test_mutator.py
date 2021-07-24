#!/usr/bin/env python3

#
# test_mutator.py
# Author: Patrick Bannister
# Unit tests for L7R dice simulator mutators
#

import unittest

from dice.mutator import ShosuroMutator

class TestShosuroMutator(unittest.TestCase):
  def test_no_unkept(self):
    m = ShosuroMutator(10, 10)
    pool = [1 for i in range(10)]
    self.assertTrue(m.mutate(pool) == (10, 0))

  def test_some_unkept(self):
    m = ShosuroMutator(2, 1)
    self.assertTrue(m.mutate([1, 2]) == (3, 1))
    m = ShosuroMutator(3, 1)
    self.assertTrue(m.mutate([1, 2, 3]) == (6, 3))
    m = ShosuroMutator(3, 2)
    self.assertTrue(m.mutate([1, 2, 3]) == (6, 1))

  def test_mutator(self):
    m = ShosuroMutator(6, 3)
    self.assertTrue(m.mutate([1, 2, 3, 4, 5, 6]) == (21, 6))
    self.assertTrue(m.mutate([1, 1, 1, 6, 6, 6]) == (21, 3))
    self.assertTrue(m.mutate([1, 1, 1, 1, 1, 1]) == (6, 3))
    m2 = ShosuroMutator(6, 2)
    self.assertTrue(m2.mutate([1, 1, 1, 1, 1, 1]) == (5, 3))
    m3 = ShosuroMutator(10, 5)
    self.assertTrue(m3.mutate([1 for i in range(10)]) == (8, 3))
    self.assertTrue(m3.mutate([i for i in range(1, 11)]) == (46, 6))


if (__name__ == '__main__'):
  unittest.main()

