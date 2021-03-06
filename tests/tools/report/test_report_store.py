"""Testing of module report."""
# pylint: disable=no-self-use, invalid-name, redundant-unittest-assert
import unittest
import time
from datetime import datetime, timedelta

from hamcrest import assert_that, equal_to
from spline.tools.report.collector import Store, CollectorUpdate


class TestReportStore(unittest.TestCase):
    """Testing of class Store."""

    def test_update_first(self):
        """Testing creating a stage."""
        store = Store()
        item = CollectorUpdate(
            stage='Build', status='started',
            timestamp=int(time.time()), information={'language': 'java'})
        store.update(item)

        stage = store.get_stage('default', 'Build')
        assert_that(stage.stage, equal_to('Build'))

        assert_that(store.count_matrixes(), equal_to(1))
        assert_that(store.count_stages('default'), equal_to(1))

    def test_clear(self):
        """Testing deletion of data."""
        store = Store()
        store.data = {'test': 'test'}
        store.clear()
        assert_that(len(store.data), equal_to(0))

    def test_update_existing(self):
        """Testing updating an existing stage."""
        store = Store()
        item = CollectorUpdate(
            stage='Build', status='started',
            timestamp=int(time.time()), information={'language': 'java'})
        store.update(item)

        item = CollectorUpdate(
            stage='Build', status='succeeded',
            timestamp=int(time.time()))
        store.update(item)

        assert_that(store.count_matrixes(), equal_to(1))
        assert_that(store.count_stages('default'), equal_to(1))

        stage = store.get_stage('default', 'Build')
        assert_that(stage.stage, equal_to('Build'))
        assert_that(stage.status, equal_to('succeeded'))
        assert_that(len(stage.events), equal_to(2))

    def test_not_existing_stage(self):
        """Testing get_stage for a stage that does not exist."""
        store = Store()
        item = CollectorUpdate(
            stage='Build', status='started',
            timestamp=int(time.time()), information={'language': 'java'})
        store.update(item)

        stage = store.get_stage('default', 'Deploy')
        assert_that(stage, equal_to(None))

    def test_not_existing_matrix(self):
        """Testing get_stage for a matrix that does not exist."""
        store = Store()
        item = CollectorUpdate(
            stage='Build', status='started',
            timestamp=int(time.time()), information={'language': 'java'})
        store.update(item)

        stage = store.get_stage('test', 'Build')
        assert_that(stage, equal_to(None))

    def test_configure(self):
        """Testing assigning the document."""
        store = Store()
        store.configure({'test': 'test'})
        # no magic ... document is used by the templates (that's all)
        assert_that(store.document, equal_to({'test': 'test'}))

    def test_matrix_duration(self):
        """Testing matrix duration."""
        now = datetime.now()
        timestamp_started = int(time.mktime(now.timetuple()))
        timestamp_succeeded = int(time.mktime((now + timedelta(seconds=60)).timetuple()))

        store = Store()
        assert_that(store.get_duration('default'), equal_to(0))

        item = CollectorUpdate(
            stage='Build', status='started', timestamp=timestamp_started, information={'language': 'java'})
        store.update(item)
        assert_that(store.get_duration('default'), equal_to(0))

        item = CollectorUpdate(stage='Build', status='succeeded', timestamp=timestamp_succeeded)
        store.update(item)

        duration = store.get_duration('default')
        assert_that(duration >= 59 and duration <= 61, equal_to(True))
