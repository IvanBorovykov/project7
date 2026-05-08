from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Meeting, MeetingParticipant
from ..repositories.meetings import MeetingRepository
from ..repositories.users import UserRepository
from .livekit import LiveKitFacade
from .notifications import NotificationService


class MeetingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.meetings = MeetingRepository(session)
        self.users = UserRepository(session)
        self.notifications = NotificationService(session)
        self.video_provider = LiveKitFacade()

    def list_for_user(self, user_id: int) -> list[Meeting]:
        return self.meetings.list_for_user(user_id)

    def upcoming_for_user(self, user_id: int, limit: int = 5) -> list[Meeting]:
        return self.meetings.upcoming_for_user(user_id, limit)

    def get(self, meeting_id: int) -> Meeting | None:
        return self.meetings.get(meeting_id)

    def create_meeting(
        self,
        *,
        organizer_id: int,
        title: str,
        description: str,
        starts_at_raw: str,
        duration_minutes: int,
        participant_ids: list[int],
        recording_enabled: bool,
    ) -> Meeting:
        title = title.strip()
        if not title:
            raise ValueError("Meeting title is required.")
        starts_at = datetime.fromisoformat(starts_at_raw)
        unique_participants = sorted(set(participant_ids + [organizer_id]))
        if len(unique_participants) > 30:
            raise ValueError("Meeting cannot have more than 30 participants.")

        meeting = self.meetings.create(
            title=title,
            description=description.strip(),
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            organizer_id=organizer_id,
            room_name="pending-room-name",
            recording_enabled=recording_enabled,
        )
        meeting.room_name = self.video_provider.generate_room_name(meeting_id=meeting.id, title=meeting.title)

        for user_id in unique_participants:
            status = "accepted" if user_id == organizer_id else "pending"
            self.meetings.add_participant(meeting_id=meeting.id, user_id=user_id, status=status)

        if recording_enabled:
            self.meetings.save_recording(meeting_id=meeting.id, status="pending", external_url=None)

        for user_id in unique_participants:
            if user_id == organizer_id:
                continue
            self.notifications.create(
                user_id=user_id,
                kind="meeting_invite",
                content=f"You were invited to meeting '{meeting.title}'.",
            )

        self.session.flush()
        return self.meetings.get(meeting.id) or meeting

    def update_participation(self, *, meeting_id: int, user_id: int, status: str) -> MeetingParticipant:
        if status not in {"accepted", "declined"}:
            raise ValueError("Invalid status.")

        participant = self.meetings.get_participant(meeting_id=meeting_id, user_id=user_id)
        if participant is None:
            raise ValueError("Participant not found.")

        participant.status = status
        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            raise ValueError("Meeting not found.")

        self.notifications.create(
            user_id=meeting.organizer_id,
            kind="meeting_response",
            content=f"{participant.user.full_name} {status} invitation for '{meeting.title}'.",
        )
        self.session.flush()
        return participant

    def save_recording(self, *, meeting_id: int, status: str, external_url: str | None) -> None:
        self.meetings.save_recording(meeting_id=meeting_id, status=status, external_url=external_url)
