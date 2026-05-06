"""
Unit tests for helper functions and business logic.

Currently the application has minimal helper functions as most logic is
integrated into endpoints. This file serves as a template for testing
extracted helper functions and validations in the future.
"""

import pytest
from pathlib import Path
import sys

# Add src directory to path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import activities


class TestActivityDataStructure:
    """Test suite for activity data structure and integrity"""

    def test_all_activities_have_required_fields(self):
        """
        ARRANGE: Activity dictionary from app
        ACT: Check each activity
        ASSERT: All activities have required fields
        """
        # ARRANGE
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # ACT & ASSERT
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict), f"{activity_name} is not a dict"
            
            # Check all required fields exist
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing field: {field}"
            
            # Validate field types
            assert isinstance(activity_data["description"], str), f"{activity_name} description not string"
            assert isinstance(activity_data["schedule"], str), f"{activity_name} schedule not string"
            assert isinstance(activity_data["max_participants"], int), f"{activity_name} max_participants not int"
            assert isinstance(activity_data["participants"], list), f"{activity_name} participants not list"

    def test_all_participants_are_email_strings(self):
        """
        ARRANGE: Participants lists from all activities
        ACT: Check each participant entry
        ASSERT: All participants are email-format strings
        """
        # ARRANGE
        # (activities are imported from app.py)

        # ACT & ASSERT
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                # Simple email validation: contains @
                assert isinstance(participant, str), f"{activity_name}: participant not string"
                assert "@" in participant, f"{activity_name}: participant not email format"

    def test_max_participants_positive_integer(self):
        """
        ARRANGE: max_participants values from all activities
        ACT: Check each value
        ASSERT: All max_participants are positive integers
        """
        # ARRANGE
        # (activities are imported from app.py)

        # ACT & ASSERT
        for activity_name, activity_data in activities.items():
            max_participants = activity_data["max_participants"]
            assert isinstance(max_participants, int), f"{activity_name}: max_participants not int"
            assert max_participants > 0, f"{activity_name}: max_participants not positive"

    def test_participants_count_not_exceeds_max(self):
        """
        ARRANGE: Activities with initial participants
        ACT: Check each activity
        ASSERT: Current participant count does not exceed max_participants
        """
        # ARRANGE
        # (activities are imported from app.py)

        # ACT & ASSERT
        for activity_name, activity_data in activities.items():
            current_count = len(activity_data["participants"])
            max_count = activity_data["max_participants"]
            assert current_count <= max_count, \
                f"{activity_name}: {current_count} participants exceed max of {max_count}"
