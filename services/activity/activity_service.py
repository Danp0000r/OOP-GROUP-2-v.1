from models.activity import Activity
from database.db import db
from services.base_service import BusinessLogicService
import logging

logger = logging.getLogger(__name__)


class ActivityService(BusinessLogicService):

    def execute(self, activity_type, user_id, description):
        return self._create_activity(user_id, activity_type, description)

    def _create_activity(self, user_id, activity_type, description):
        try:
            activity = Activity.log_activity(user_id, activity_type, description)
            self._cache_result(f"activity_{activity.activity_id}", activity)
            return activity
        except Exception as e:
            self._log_error(
                f"Failed to create activity",
                {"user_id": user_id, "type": activity_type},
            )
            logger.error(f"Error creating activity: {str(e)}")
            return None

    @staticmethod
    def log_profile_update(user_id, changes=None):
        try:
            description = "Updated profile"
            if changes:
                description += f": {', '.join(changes)}"

            return Activity.log_activity(user_id, "profile_update", description)
        except Exception as e:
            logger.error(f"Error logging profile update: {str(e)}")
            return None

    @staticmethod
    def log_password_change(user_id):
        try:
            return Activity.log_activity(user_id, "password_change", "Changed password")
        except Exception as e:
            logger.error(f"Error logging password change: {str(e)}")
            return None

    @staticmethod
    def log_build_created(user_id, build_name):
        try:
            return Activity.log_activity(
                user_id, "build_created", f"Created build: {build_name}"
            )
        except Exception as e:
            logger.error(f"Error logging build creation: {str(e)}")
            return None

    @staticmethod
    def log_build_updated(user_id, build_name):
        try:
            return Activity.log_activity(
                user_id, "build_updated", f"Updated build: {build_name}"
            )
        except Exception as e:
            logger.error(f"Error logging build update: {str(e)}")
            return None

    @staticmethod
    def log_build_deleted(user_id, build_name):
        try:
            return Activity.log_activity(
                user_id, "build_deleted", f"Deleted build: {build_name}"
            )
        except Exception as e:
            logger.error(f"Error logging build deletion: {str(e)}")
            return None

    @staticmethod
    def log_compatibility_check(user_id, build_name, status):
        try:
            return Activity.log_activity(
                user_id,
                "compatibility_check",
                f"Checked compatibility for {build_name} - Result: {status}",
            )
        except Exception as e:
            logger.error(f"Error logging compatibility check: {str(e)}")
            return None

    @staticmethod
    def log_compatibility_fix(user_id, build_name):
        try:
            return Activity.log_activity(
                user_id,
                "compatibility_fix",
                f"Applied compatibility fixes to {build_name}",
            )
        except Exception as e:
            logger.error(f"Error logging compatibility fix: {str(e)}")
            return None

    @staticmethod
    def log_build_shared(user_id, build_name, shared_with="public"):
        try:
            return Activity.log_activity(
                user_id,
                "build_shared",
                f"Shared build '{build_name}' with {shared_with}",
            )
        except Exception as e:
            logger.error(f"Error logging build share: {str(e)}")
            return None

    @staticmethod
    def log_comparison(user_id, compared_items, comparison_type="builds"):
        try:
            return Activity.log_activity(
                user_id,
                "comparison_made",
                f"Compared {compared_items} {comparison_type}",
            )
        except Exception as e:
            logger.error(f"Error logging comparison: {str(e)}")
            return None

    @staticmethod
    def log_questionnaire_completed(user_id):
        try:
            return Activity.log_activity(
                user_id,
                "questionnaire_completed",
                "Completed PC questionnaire for recommendations",
            )
        except Exception as e:
            logger.error(f"Error logging questionnaire: {str(e)}")
            return None

    @staticmethod
    def log_custom_activity(user_id, action_type, description):
        try:
            return Activity.log_activity(user_id, action_type, description)
        except Exception as e:
            logger.error(f"Error logging custom activity: {str(e)}")
            return None

    @staticmethod
    def get_user_activities(user_id, limit=10):
        try:
            return Activity.get_recent_activities(user_id, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving activities: {str(e)}")
            return []

    @staticmethod
    def get_activity_stats(user_id):
        try:
            all_activities = Activity.query.filter_by(user_id=user_id).all()

            # Count by action type
            stats = {"total_activities": len(all_activities), "by_type": {}}

            for activity in all_activities:
                action_type = activity.action_type
                stats["by_type"][action_type] = stats["by_type"].get(action_type, 0) + 1

            return stats
        except Exception as e:
            logger.error(f"Error getting activity stats: {str(e)}")
            return {"total_activities": 0, "by_type": {}}

    @staticmethod
    def clear_user_activities(user_id):
        try:
            deleted = Activity.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            return deleted
        except Exception as e:
            logger.error(f"Error clearing activities: {str(e)}")
            return 0
