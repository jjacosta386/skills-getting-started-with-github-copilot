"""
Integration tests for FastAPI activity endpoints using AAA (Arrange-Act-Assert) pattern.

Tests cover:
- GET /activities - Retrieve all activities
- POST /activities/{activity_name}/signup - Sign up a student for an activity
- DELETE /activities/{activity_name}/participants - Remove a student from an activity
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_all_activities_successfully(self, client: TestClient):
        """
        ARRANGE: Client is ready
        ACT: Make a GET request to /activities
        ASSERT: Response contains all 9 activities with correct structure
        """
        # ARRANGE
        expected_activity_count = 9

        # ACT
        response = client.get("/activities")

        # ASSERT
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Basketball Team" in activities
        assert activities["Chess Club"]["max_participants"] == 12
        assert isinstance(activities["Chess Club"]["participants"], list)

    def test_get_activities_includes_existing_participants(self, client: TestClient):
        """
        ARRANGE: Activities have pre-existing participants
        ACT: Make a GET request to /activities
        ASSERT: Response includes all pre-existing participants
        """
        # ARRANGE
        # (activities are seeded in conftest.py)

        # ACT
        response = client.get("/activities")

        # ASSERT
        activities = response.json()
        chess_club = activities["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 2


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client: TestClient):
        """
        ARRANGE: New student email, empty Basketball Team
        ACT: Sign up student for Basketball Team
        ASSERT: Response confirms signup, participant added to activity
        """
        # ARRANGE
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]

    def test_signup_for_activity_with_existing_participants(self, client: TestClient):
        """
        ARRANGE: Activity already has participants
        ACT: Sign up new student for Chess Club
        ASSERT: New participant added while existing ones remain
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "newchessplayer@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants
        assert "michael@mergington.edu" in participants  # Original participant still there
        assert "daniel@mergington.edu" in participants  # Original participant still there
        assert len(participants) == 3

    def test_signup_for_nonexistent_activity_returns_404(self, client: TestClient):
        """
        ARRANGE: Activity does not exist
        ACT: Attempt to sign up for non-existent activity
        ASSERT: Returns 404 with appropriate error message
        """
        # ARRANGE
        activity_name = "NonExistent Activity"
        email = "student@mergington.edu"

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self, client: TestClient):
        """
        ARRANGE: Student already signed up for Chess Club
        ACT: Attempt to sign up same student again
        ASSERT: Returns 400 with appropriate error message
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in participants

        # ACT
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 400
        assert "Student already signed up for this activity" in response.json()["detail"]

    def test_signup_increases_participant_count(self, client: TestClient):
        """
        ARRANGE: Empty activity, track initial participant count
        ACT: Sign up 3 students sequentially
        ASSERT: Participant count increases correctly after each signup
        """
        # ARRANGE
        activity_name = "Basketball Team"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # ACT & ASSERT
        for i, email in enumerate(emails):
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
            
            # Verify count increased
            activities_response = client.get("/activities")
            current_count = len(activities_response.json()[activity_name]["participants"])
            assert current_count == initial_count + i + 1


class TestRemoveParticipant:
    """Test suite for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_success(self, client: TestClient):
        """
        ARRANGE: Participant exists in Chess Club
        ACT: Remove participant from Chess Club
        ASSERT: Response confirms removal, participant no longer in activity
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
        assert "daniel@mergington.edu" in activities_response.json()[activity_name]["participants"]

    def test_remove_participant_other_participants_unaffected(self, client: TestClient):
        """
        ARRANGE: Chess Club has 2 participants
        ACT: Remove one participant
        ASSERT: Other participant remains in activity
        """
        # ARRANGE
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email_to_remove}
        )

        # ASSERT
        assert response.status_code == 200
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email_to_remove not in participants
        assert email_to_keep in participants

    def test_remove_participant_from_nonexistent_activity_returns_404(self, client: TestClient):
        """
        ARRANGE: Activity does not exist
        ACT: Attempt to remove participant from non-existent activity
        ASSERT: Returns 404 with appropriate error message
        """
        # ARRANGE
        activity_name = "NonExistent Activity"
        email = "student@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_nonexistent_participant_returns_404(self, client: TestClient):
        """
        ARRANGE: Participant not in Chess Club
        ACT: Attempt to remove non-existent participant
        ASSERT: Returns 404 with appropriate error message
        """
        # ARRANGE
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # ACT
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # ASSERT
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_all_participants_sequentially(self, client: TestClient):
        """
        ARRANGE: Chess Club has 2 participants
        ACT: Remove both participants
        ASSERT: Activity becomes empty after each removal
        """
        # ARRANGE
        activity_name = "Chess Club"
        emails = ["michael@mergington.edu", "daniel@mergington.edu"]

        # ACT & ASSERT
        for i, email in enumerate(emails):
            response = client.delete(
                f"/activities/{activity_name}/participants",
                params={"email": email}
            )
            assert response.status_code == 200
            
            # Verify participant removed
            activities_response = client.get("/activities")
            participants = activities_response.json()[activity_name]["participants"]
            assert email not in participants
            assert len(participants) == len(emails) - i - 1


class TestEdgeCases:
    """Test suite for edge cases and integration scenarios"""

    def test_signup_then_remove_same_participant(self, client: TestClient):
        """
        ARRANGE: Basketball Team is empty
        ACT: Sign up a participant, then remove them
        ASSERT: Activity is empty again
        """
        # ARRANGE
        activity_name = "Basketball Team"
        email = "tempstudent@mergington.edu"

        # ACT - Sign up
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200

        # ACT - Remove
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        assert response.status_code == 200

        # ASSERT
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]

    def test_multiple_activities_independent_state(self, client: TestClient):
        """
        ARRANGE: Two different activities
        ACT: Modify participants in both activities
        ASSERT: Changes in one activity don't affect the other
        """
        # ARRANGE
        activity1 = "Basketball Team"
        activity2 = "Soccer Club"
        email = "athlete@mergington.edu"

        # ACT - Sign up for activity 1
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # ACT - Sign up for activity 2
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )
        assert response2.status_code == 200

        # ASSERT - Both activities have the email
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]

        # ACT - Remove from activity 1
        client.delete(
            f"/activities/{activity1}/participants",
            params={"email": email}
        )

        # ASSERT - Only activity 2 still has the email
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity1]["participants"]
        assert email in activities[activity2]["participants"]

    def test_email_case_sensitive(self, client: TestClient):
        """
        ARRANGE: Sign up with lowercase email
        ACT: Attempt to sign up with uppercase version of same email
        ASSERT: Treated as different emails (case-sensitive)
        """
        # ARRANGE
        activity_name = "Basketball Team"
        email_lower = "student@mergington.edu"
        email_upper = "STUDENT@MERGINGTON.EDU"

        # ACT - Sign up with lowercase
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_lower}
        )
        assert response1.status_code == 200

        # ACT - Sign up with uppercase (should succeed since case differs)
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_upper}
        )
        assert response2.status_code == 200

        # ASSERT - Both emails are in participants
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email_lower in participants
        assert email_upper in participants
