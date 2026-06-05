import os
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from services.activity.activity_service import ActivityService


class ActivityServiceTestCase(unittest.TestCase):

    def test_execute_caches_activity_and_returns_object(self):
        service = ActivityService()
        fake_activity = MagicMock()
        fake_activity.activity_id = 123

        with patch('services.activity.activity_service.Activity.log_activity', return_value=fake_activity) as mocked_log:
            result = service.execute('build_created', 1, 'Created build: Test Build')

        self.assertIs(result, fake_activity)
        mocked_log.assert_called_once_with(1, 'build_created', 'Created build: Test Build')
        self.assertIs(service._get_cached('activity_123'), fake_activity)

    def test_create_activity_returns_none_on_exception_and_logs_error(self):
        service = ActivityService()

        with patch('services.activity.activity_service.Activity.log_activity', side_effect=Exception('DB failure')) as mocked_log:
            result = service.execute('build_created', 1, 'Created build: Test Build')

        self.assertIsNone(result)
        mocked_log.assert_called_once_with(1, 'build_created', 'Created build: Test Build')
        self.assertTrue(service.get_errors())
        self.assertEqual(service.get_errors()[0]['message'], 'Failed to create activity')

    def test_log_profile_update_with_changes_builds_description(self):
        fake_activity = MagicMock()
        with patch('services.activity.activity_service.Activity.log_activity', return_value=fake_activity) as mocked_log:
            result = ActivityService.log_profile_update(5, ['email', 'avatar'])

        self.assertIs(result, fake_activity)
        mocked_log.assert_called_once_with(5, 'profile_update', 'Updated profile: email, avatar')

    def test_log_profile_update_without_changes(self):
        fake_activity = MagicMock()
        with patch('services.activity.activity_service.Activity.log_activity', return_value=fake_activity) as mocked_log:
            result = ActivityService.log_profile_update(5, [])

        self.assertIs(result, fake_activity)
        mocked_log.assert_called_once_with(5, 'profile_update', 'Updated profile')

    def test_log_password_change_formats_description(self):
        fake_activity = MagicMock()
        with patch('services.activity.activity_service.Activity.log_activity', return_value=fake_activity) as mocked_log:
            result = ActivityService.log_password_change(7)

        self.assertIs(result, fake_activity)
        mocked_log.assert_called_once_with(7, 'password_change', 'Changed password')

    def test_log_build_actions_format_correctly(self):
        fake_activity = MagicMock()
        with patch('services.activity.activity_service.Activity.log_activity', return_value=fake_activity) as mocked_log:
            self.assertIs(ActivityService.log_build_created(2, 'Alpha'), fake_activity)
            self.assertIs(ActivityService.log_build_updated(2, 'Beta'), fake_activity)
            self.assertIs(ActivityService.log_build_deleted(2, 'Gamma'), fake_activity)

        expected_calls = [
            ((2, 'build_created', 'Created build: Alpha'),),
            ((2, 'build_updated', 'Updated build: Beta'),),
            ((2, 'build_deleted', 'Deleted build: Gamma'),),
        ]
        self.assertEqual(mocked_log.call_args_list, expected_calls)

    def test_log_compatibility_and_comparison_and_custom_actions(self):
        fake_activity = MagicMock()
        with patch('services.activity.activity_service.Activity.log_activity', return_value=fake_activity) as mocked_log:
            self.assertIs(ActivityService.log_compatibility_check(3, 'MyBuild', 'compatible'), fake_activity)
            self.assertIs(ActivityService.log_compatibility_fix(3, 'MyBuild'), fake_activity)
            self.assertIs(ActivityService.log_build_shared(3, 'MyBuild'), fake_activity)
            self.assertIs(ActivityService.log_build_shared(3, 'MyBuild', shared_with='team'), fake_activity)
            self.assertIs(ActivityService.log_comparison(3, 4, 'components'), fake_activity)
            self.assertIs(ActivityService.log_questionnaire_completed(3), fake_activity)
            self.assertIs(ActivityService.log_custom_activity(3, 'custom_action', 'Did something'), fake_activity)

        expected_calls = [
            ((3, 'compatibility_check', 'Checked compatibility for MyBuild - Result: compatible'),),
            ((3, 'compatibility_fix', 'Applied compatibility fixes to MyBuild'),),
            ((3, "build_shared", "Shared build 'MyBuild' with public"),),
            ((3, "build_shared", "Shared build 'MyBuild' with team"),),
            ((3, 'comparison_made', 'Compared 4 components'),),
            ((3, 'questionnaire_completed', 'Completed PC questionnaire for recommendations'),),
            ((3, 'custom_action', 'Did something'),),
        ]
        self.assertEqual(mocked_log.call_args_list, expected_calls)

    def test_static_methods_return_none_on_exception(self):
        methods = [
            lambda: ActivityService.log_password_change(1),
            lambda: ActivityService.log_build_created(1, 'A'),
            lambda: ActivityService.log_build_updated(1, 'A'),
            lambda: ActivityService.log_build_deleted(1, 'A'),
            lambda: ActivityService.log_compatibility_check(1, 'A', 'bad'),
            lambda: ActivityService.log_compatibility_fix(1, 'A'),
            lambda: ActivityService.log_build_shared(1, 'A'),
            lambda: ActivityService.log_comparison(1, 2),
            lambda: ActivityService.log_questionnaire_completed(1),
            lambda: ActivityService.log_custom_activity(1, 'custom_action', 'A'),
        ]

        with patch('services.activity.activity_service.Activity.log_activity', side_effect=Exception('boom')):
            for method in methods:
                self.assertIsNone(method())

    def test_get_user_activities_returns_list_on_success(self):
        fake_activities = [MagicMock(), MagicMock()]
        with patch('services.activity.activity_service.Activity.get_recent_activities', return_value=fake_activities) as mocked_get:
            result = ActivityService.get_user_activities(12, limit=5)

        self.assertEqual(result, fake_activities)
        mocked_get.assert_called_once_with(12, limit=5)

    def test_get_user_activities_returns_empty_list_on_exception(self):
        with patch('services.activity.activity_service.Activity.get_recent_activities', side_effect=Exception('DB error')) as mocked_get:
            result = ActivityService.get_user_activities(12, limit=5)

        self.assertEqual(result, [])
        mocked_get.assert_called_once_with(12, limit=5)

    def test_get_activity_stats_counts_actions_correctly(self):
        fake_activities = [MagicMock(action_type='build_created'), MagicMock(action_type='build_created'), MagicMock(action_type='password_change')]
        query_mock = MagicMock()
        query_mock.filter_by.return_value.all.return_value = fake_activities

        with patch('services.activity.activity_service.Activity') as MockActivity:
            MockActivity.query = query_mock
            result = ActivityService.get_activity_stats(7)

        self.assertEqual(result['total_activities'], 3)
        self.assertEqual(result['by_type']['build_created'], 2)
        self.assertEqual(result['by_type']['password_change'], 1)
        query_mock.filter_by.assert_called_once_with(user_id=7)

    def test_get_activity_stats_returns_defaults_on_exception(self):
        query_mock = MagicMock()
        query_mock.filter_by.side_effect = Exception('failure')

        with patch('services.activity.activity_service.Activity') as MockActivity:
            MockActivity.query = query_mock
            result = ActivityService.get_activity_stats(7)

        self.assertEqual(result, {'total_activities': 0, 'by_type': {}})

    def test_clear_user_activities_commits_and_returns_deleted_count(self):
        query_mock = MagicMock()
        query_mock.filter_by.return_value.delete.return_value = 4
        db_mock = MagicMock()

        with patch('services.activity.activity_service.Activity') as MockActivity, patch('services.activity.activity_service.db', db_mock):
            MockActivity.query = query_mock
            result = ActivityService.clear_user_activities(8)

        self.assertEqual(result, 4)
        db_mock.session.commit.assert_called_once()
        query_mock.filter_by.assert_called_once_with(user_id=8)

    def test_clear_user_activities_returns_zero_on_exception(self):
        query_mock = MagicMock()
        query_mock.filter_by.return_value.delete.side_effect = Exception('failure')
        db_mock = MagicMock()

        with patch('services.activity.activity_service.Activity') as MockActivity, patch('services.activity.activity_service.db', db_mock):
            MockActivity.query = query_mock
            result = ActivityService.clear_user_activities(8)

        self.assertEqual(result, 0)
        db_mock.session.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
