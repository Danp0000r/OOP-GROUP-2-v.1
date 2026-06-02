"""
Activity Service - Centralized management of user activity logging.

Handles logging of all user actions for the recent activity feature.

OOP Implementation:
- INHERITANCE: Inherits from BusinessLogicService (which extends BaseService)
- ENCAPSULATION: Protected error logging, internal activity creation
- POLYMORPHISM: Implements abstract execute() method
- ABSTRACTION: Provides clean logging interface hiding Activity model details
"""

from models.activity import Activity
from database.db import db
from services.base_service import BusinessLogicService
import logging

logger = logging.getLogger(__name__)


class ActivityService(BusinessLogicService):
    """
    Service for managing user activity logging.
    
    Demonstrates OOP pillars:
    - INHERITANCE: Extends BusinessLogicService
    - POLYMORPHISM: Implements execute() with activity logging logic
    - ENCAPSULATION: Protected methods for internal activity handling
    """
    
    def execute(self, activity_type, user_id, description):
        """
        Execute activity logging. Implements abstract method from BaseService.
        
        Args:
            activity_type: Type of activity (profile_update, build_created, etc)
            user_id: ID of user performing action
            description: Description of the action
            
        Returns:
            Activity object or None if failed
        """
        return self._create_activity(user_id, activity_type, description)
    
    def _create_activity(self, user_id, activity_type, description):
        """
        Protected method: Create activity record (ENCAPSULATION).
        
        Args:
            user_id: ID of user
            activity_type: Type of activity
            description: Activity description
            
        Returns:
            Activity object or None
        """
        try:
            activity = Activity.log_activity(user_id, activity_type, description)
            self._cache_result(f"activity_{activity.activity_id}", activity)
            return activity
        except Exception as e:
            self._log_error(f"Failed to create activity", {"user_id": user_id, "type": activity_type})
            logger.error(f"Error creating activity: {str(e)}")
            return None

    @staticmethod
    def log_profile_update(user_id, changes=None):
        """
        Log when user updates their profile.
        
        Args:
            user_id: ID of the user
            changes: List of fields changed (optional)
        
        Returns:
            Activity object or None if failed
        """
        try:
            description = "Updated profile"
            if changes:
                description += f": {', '.join(changes)}"
            
            return Activity.log_activity(
                user_id,
                "profile_update",
                description
            )
        except Exception as e:
            logger.error(f"Error logging profile update: {str(e)}")
            return None

    @staticmethod
    def log_password_change(user_id):
        """
        Log when user changes their password.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "password_change",
                "Changed password"
            )
        except Exception as e:
            logger.error(f"Error logging password change: {str(e)}")
            return None

    @staticmethod
    def log_build_created(user_id, build_name):
        """
        Log when user creates a new build.
        
        Args:
            user_id: ID of the user
            build_name: Name of the build
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "build_created",
                f"Created build: {build_name}"
            )
        except Exception as e:
            logger.error(f"Error logging build creation: {str(e)}")
            return None

    @staticmethod
    def log_build_updated(user_id, build_name):
        """
        Log when user updates an existing build.
        
        Args:
            user_id: ID of the user
            build_name: Name of the build
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "build_updated",
                f"Updated build: {build_name}"
            )
        except Exception as e:
            logger.error(f"Error logging build update: {str(e)}")
            return None

    @staticmethod
    def log_build_deleted(user_id, build_name):
        """
        Log when user deletes a build.
        
        Args:
            user_id: ID of the user
            build_name: Name of the build
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "build_deleted",
                f"Deleted build: {build_name}"
            )
        except Exception as e:
            logger.error(f"Error logging build deletion: {str(e)}")
            return None

    @staticmethod
    def log_compatibility_check(user_id, build_name, status):
        """
        Log when user checks build compatibility.
        
        Args:
            user_id: ID of the user
            build_name: Name of the build checked
            status: Result status (compatible/incompatible/needs_fix)
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "compatibility_check",
                f"Checked compatibility for {build_name} - Result: {status}"
            )
        except Exception as e:
            logger.error(f"Error logging compatibility check: {str(e)}")
            return None

    @staticmethod
    def log_compatibility_fix(user_id, build_name):
        """
        Log when user applies compatibility fixes to a build.
        
        Args:
            user_id: ID of the user
            build_name: Name of the build
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "compatibility_fix",
                f"Applied compatibility fixes to {build_name}"
            )
        except Exception as e:
            logger.error(f"Error logging compatibility fix: {str(e)}")
            return None

    @staticmethod
    def log_build_shared(user_id, build_name, shared_with="public"):
        """
        Log when user shares a build.
        
        Args:
            user_id: ID of the user
            build_name: Name of the build
            shared_with: Who the build is shared with (e.g., 'public', email, username)
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "build_shared",
                f"Shared build '{build_name}' with {shared_with}"
            )
        except Exception as e:
            logger.error(f"Error logging build share: {str(e)}")
            return None

    @staticmethod
    def log_comparison(user_id, compared_items, comparison_type="builds"):
        """
        Log when user compares items (builds or components).
        
        Args:
            user_id: ID of the user
            compared_items: Number of items compared
            comparison_type: Type of comparison (builds/components)
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "comparison_made",
                f"Compared {compared_items} {comparison_type}"
            )
        except Exception as e:
            logger.error(f"Error logging comparison: {str(e)}")
            return None

    @staticmethod
    def log_questionnaire_completed(user_id):
        """
        Log when user completes the PC questionnaire.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(
                user_id,
                "questionnaire_completed",
                "Completed PC questionnaire for recommendations"
            )
        except Exception as e:
            logger.error(f"Error logging questionnaire: {str(e)}")
            return None

    @staticmethod
    def log_custom_activity(user_id, action_type, description):
        """
        Log a custom activity with specified action type and description.
        
        Args:
            user_id: ID of the user
            action_type: Type of action (e.g., 'custom_action')
            description: Description of the activity
        
        Returns:
            Activity object or None if failed
        """
        try:
            return Activity.log_activity(user_id, action_type, description)
        except Exception as e:
            logger.error(f"Error logging custom activity: {str(e)}")
            return None

    @staticmethod
    def get_user_activities(user_id, limit=10):
        """
        Get recent activities for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of activities to return (default: 10)
        
        Returns:
            List of Activity objects
        """
        try:
            return Activity.get_recent_activities(user_id, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving activities: {str(e)}")
            return []

    @staticmethod
    def get_activity_stats(user_id):
        """
        Get activity statistics for a user.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Dictionary with activity statistics
        """
        try:
            all_activities = Activity.query.filter_by(user_id=user_id).all()
            
            # Count by action type
            stats = {
                "total_activities": len(all_activities),
                "by_type": {}
            }
            
            for activity in all_activities:
                action_type = activity.action_type
                stats["by_type"][action_type] = stats["by_type"].get(action_type, 0) + 1
            
            return stats
        except Exception as e:
            logger.error(f"Error getting activity stats: {str(e)}")
            return {"total_activities": 0, "by_type": {}}

    @staticmethod
    def clear_user_activities(user_id):
        """
        Clear all activities for a user (use with caution).
        
        Args:
            user_id: ID of the user
        
        Returns:
            Number of activities deleted
        """
        try:
            deleted = Activity.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            return deleted
        except Exception as e:
            logger.error(f"Error clearing activities: {str(e)}")
            return 0
