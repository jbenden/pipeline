"""Testing of module condition for final conditions (after rendering."""
# pylint: disable=no-self-use, invalid-name, too-many-public-methods
import unittest
from hamcrest import assert_that, equal_to
from spline.tools.condition import Condition


class TestFinalCondition(unittest.TestCase):
    """Testing of final conditions after rendering."""

    def test_empty_condition(self):
        """An empty condition evaluates to True."""
        assert_that(Condition.evaluate(''), equal_to(True))

    def test_num_equal_num(self):
        """Testing two integer to be equal."""
        assert_that(Condition.evaluate('2 == 2'), equal_to(True))
        assert_that(Condition.evaluate('2 == 3'), equal_to(False))

    def test_num_not_equal_num(self):
        """Testing two integer to be not equal."""
        assert_that(Condition.evaluate('not 2 == 2'), equal_to(False))
        assert_that(Condition.evaluate('not 2 == 3'), equal_to(True))

    def test_str_equal_str(self):
        """Testing two strings to be equal."""
        assert_that(Condition.evaluate('"hello" == "hello"'), equal_to(True))
        assert_that(Condition.evaluate('  "hello"  ==  "hello"  '), equal_to(True))

        # not equal
        assert_that(Condition.evaluate('"hello" == "hallo"'), equal_to(False))
        # wrong format
        assert_that(Condition.evaluate('"hello" == hello'), equal_to(False))

    def test_str_not_equal_str(self):
        """Testing two strings to be not equal."""
        assert_that(Condition.evaluate('not "hello" == "hallo"'), equal_to(True))
        assert_that(Condition.evaluate('  not  "hello"  ==  "hallo"  '), equal_to(True))
        # is equal
        assert_that(Condition.evaluate('not "hello" == "hello"'), equal_to(False))
        # wrong format
        assert_that(Condition.evaluate('NOT "hello" == "hello"'), equal_to(False))

    def test_str_in_str_list(self):
        """Testing string in string list."""
        assert_that(Condition.evaluate('"apple" in ["apple", "banana", "kiwi"]'), equal_to(True))
        assert_that(Condition.evaluate('"apple" in ["banana", "kiwi"]'), equal_to(False))

    def test_str_nin_str_list(self):
        """Testing string not in string list."""
        assert_that(Condition.evaluate('"apple" not in ["apple", "banana", "kiwi"]'), equal_to(False))
        assert_that(Condition.evaluate('"apple" not in ["banana", "kiwi"]'), equal_to(True))

    def test_num_in_num_list(self):
        """Testing integer in integer list."""
        assert_that(Condition.evaluate('2 in [2, 4, 6, 8]'), equal_to(True))
        assert_that(Condition.evaluate('2 in [3, 5, 7, 9]'), equal_to(False))

    def test_num_nin_num_list(self):
        """Testing integer not in integer list."""
        assert_that(Condition.evaluate('2 not in [2, 4, 6, 8]'), equal_to(False))
        assert_that(Condition.evaluate('2 not in [3, 5, 7, 9]'), equal_to(True))

    def test_num_gt_num(self):
        """Testing integer greater than another integer."""
        assert_that(Condition.evaluate('3 > 2'), equal_to(True))
        assert_that(Condition.evaluate('2 > 2'), equal_to(False))

    def test_num_gte_num(self):
        """Testing integer greater or equal than another integer."""
        assert_that(Condition.evaluate('3 >= 2'), equal_to(True))
        assert_that(Condition.evaluate('2 >= 2'), equal_to(True))
        assert_that(Condition.evaluate('1 >= 2'), equal_to(False))

    def test_num_lt_num(self):
        """Testing integer less than another integer."""
        assert_that(Condition.evaluate('2 < 3'), equal_to(True))
        assert_that(Condition.evaluate('2 < 2'), equal_to(False))

    def test_num_lte_num(self):
        """Testing integer less or equal than another integer."""
        assert_that(Condition.evaluate('2 <= 3'), equal_to(True))
        assert_that(Condition.evaluate('2 <= 2'), equal_to(True))
        assert_that(Condition.evaluate('2 <= 1'), equal_to(False))

    def test_special(self):
        """Mainly covers special cases like nested lists."""
        assert_that(Condition.evaluate('2 in [2, [3, 4]]'), equal_to(False))
        assert_that(Condition.evaluate('2 3 4 5'), equal_to(False))
        assert_that(Condition.evaluate('2 in []'), equal_to(False))
