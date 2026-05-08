from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Meeting, MeetingParticipant, Recording


class MeetingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id: int) -> list[Meeting]:
        query = (
            select(Meeting)
            .options(
                selectinload(Meeting.organizer),
                selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
                selectinload(Meeting.recording),
            )
            .join(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
            .where(MeetingParticipant.user_id == user_id)
            .order_by(Meeting.starts_at)
        )
        return list(self.session.scalars(query).unique())

    def upcoming_for_user(self, user_id: int, limit: int = 5) -> list[Meeting]:
        query = (
            select(Meeting)
            .options(selectinload(Meeting.organizer))
            .join(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
            .where(MeetingParticipant.user_id == user_id, Meeting.starts_at >= datetime.utcnow())
            .order_by(Meeting.starts_at)
            .limit(limit)
        )
        return list(self.session.scalars(query))

    def get(self, meeting_id: int) -> Meeting | None:
        query = (
            select(Meeting)
            .options(
                selectinload(Meeting.organizer),
                selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
                selectinload(Meeting.recording),
            )
            .where(Meeting.id == meeting_id)
        )
        return self.session.scalar(query)

    def create(
        self,
        *,
        title: str,
        description: str,
        starts_at: datetime,
        duration_minutes: int,
        organizer_id: int,
        room_name: str,
        recording_enabled: bool,
    ) -> Meeting:
        meeting = Meeting(
            title=title,
            description=description,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            organizer_id=organizer_id,
            room_name=room_name,
            recording_enabled=recording_enabled,
        )
        self.session.add(meeting)
        self.session.flush()
        return meeting

    def add_participant(self, *, meeting_id: int, user_id: int, status: str = "pending") -> MeetingParticipant:
        participant = MeetingParticipant(meeting_id=meeting_id, user_id=user_id, status=status)
        self.session.add(participant)
        self.session.flush()
        return participant

    def get_participant(self, *, meeting_id: int, user_id: int) -> MeetingParticipant | None:
        query = select(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user_id,
        )
        return self.session.scalar(query)

    def save_recording(self, *, meeting_id: int, status: str, external_url: str | None) -> Recording:
        meeting = self.get(meeting_id)
        if meeting is None:
            raise ValueError("Meeting not found.")

        recording = meeting.recording
        if recording is None:
            recording = Recording(meeting_id=meeting_id, status=status, external_url=external_url)
            self.session.add(recording)
        else:
            recording.status = status
            recording.external_url = external_url
        self.session.flush()
        return recording
