from __future__ import annotations

from dataclasses import dataclass

from livekit import api

from ..config import LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL


@dataclass(frozen=True, slots=True)
class LiveKitRoomConfig:
    room_name: str
    server_url: str
    display_name: str
    is_configured: bool


class LiveKitConfigurationError(RuntimeError):
    pass


class LiveKitFacade:
    def build_room_config(self, *, room_name: str, display_name: str) -> LiveKitRoomConfig:
        safe_room = room_name.strip().replace(" ", "-")
        return LiveKitRoomConfig(
            room_name=safe_room,
            server_url=LIVEKIT_URL,
            display_name=display_name,
            is_configured=bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET and LIVEKIT_URL),
        )

    def generate_room_name(self, *, meeting_id: int, title: str) -> str:
        slug = "-".join(title.lower().split())[:40] or "meeting"
        return f"lab7-{meeting_id}-{slug}"

    def generate_participant_token(
        self,
        *,
        room_name: str,
        participant_identity: str,
        participant_name: str,
    ) -> str:
        if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET or not LIVEKIT_URL:
            raise LiveKitConfigurationError(
                "LiveKit is not configured. Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET."
            )

        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token = token.with_grants(api.VideoGrants(room_join=True, room=room_name))
        token = token.with_identity(participant_identity)
        token = token.with_name(participant_name)
        return token.to_jwt()
