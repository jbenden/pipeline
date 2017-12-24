"""Testing of module event."""
# pylint: disable=no-self-use, invalid-name
import unittest
from logging import Logger
from hamcrest import assert_that, equal_to
from spline.tools.event import Event
from spline.tools.logger import NoLogger


class TestHooks(unittest.TestCase):
    """Testing of class Event."""

    def test_succeed(self):
        """Testing simple event that was successful."""
        event = Event.create(__name__)
        event.succeeded()
        assert_that(event.status, equal_to('succeeded'))
        assert_that(event.information, equal_to({}))
        assert_that(isinstance(event.logger, NoLogger), equal_to(True))

    def test_succeed_with_information(self):
        """Testing simple event that was successful."""
        event = Event.create(__name__)
        event.succeeded(stage='build')
        assert_that(event.status, equal_to('succeeded'))
        assert_that(event.information, equal_to({'stage': 'build'}))

    def test_configure_logging_enabled(self):
        """Testing configuration of logging."""
        assert_that(Event.is_logging_enabled, equal_to(False))
        Event.configure(is_logging_enabled=True)
        assert_that(Event.is_logging_enabled, equal_to(True))
        Event.configure(is_logging_enabled=False)
        assert_that(Event.is_logging_enabled, equal_to(False))

    def test_logging_enabled(self):
        """Testing instation of a concrete logger."""
        Event.configure(is_logging_enabled=True)
        event = Event.create(__name__)
        assert_that(isinstance(event.logger, Logger), equal_to(True))
        Event.configure(is_logging_enabled=False)