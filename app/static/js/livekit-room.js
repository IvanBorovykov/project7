(function () {
    const script = document.currentScript;
    const statusNode = document.getElementById("livekit-status");
    const grid = document.getElementById("video-grid");
    const joinButton = document.getElementById("join-room-btn");
    const leaveButton = document.getElementById("leave-room-btn");
    const micButton = document.getElementById("toggle-mic-btn");
    const cameraButton = document.getElementById("toggle-camera-btn");
    const screenButton = document.getElementById("toggle-screen-btn");

    if (!script || !statusNode || !grid || !joinButton || !leaveButton || !micButton || !cameraButton || !screenButton) {
        return;
    }

    const roomName = script.dataset.roomName;
    const configured = script.dataset.configured === "true";
    if (!configured) {
        joinButton.disabled = true;
        micButton.disabled = true;
        cameraButton.disabled = true;
        screenButton.disabled = true;
        leaveButton.disabled = true;
        return;
    }

    const livekit = window.LivekitClient;
    if (!livekit) {
        statusNode.textContent = "LiveKit client SDK failed to load.";
        return;
    }

    let room = null;
    let micEnabled = true;
    let cameraEnabled = true;
    let screenEnabled = false;

    function renderPlaceholder() {
        if (!grid.children.length) {
            const placeholder = document.createElement("div");
            placeholder.className = "participant-tile participant-placeholder";
            placeholder.textContent = "Connected. Waiting for participants and tracks.";
            grid.appendChild(placeholder);
        }
    }

    function clearPlaceholder() {
        const placeholder = grid.querySelector(".participant-placeholder");
        if (placeholder) {
            placeholder.remove();
        }
    }

    function tileId(participantIdentity, trackSid) {
        return `tile-${participantIdentity}-${trackSid}`;
    }

    function removeTrack(participantIdentity, trackSid) {
        const existing = document.getElementById(tileId(participantIdentity, trackSid));
        if (existing) {
            existing.remove();
        }
        renderPlaceholder();
    }

    function attachTrack(track, participant) {
        clearPlaceholder();
        const wrapper = document.createElement("div");
        wrapper.className = "participant-tile";
        wrapper.id = tileId(participant.identity, track.sid);

        const label = document.createElement("div");
        label.className = "participant-label";
        label.textContent = participant.name || participant.identity;
        wrapper.appendChild(label);

        const element = track.attach();
        element.classList.add("participant-media");
        element.autoplay = true;
        element.playsInline = true;
        wrapper.appendChild(element);
        grid.appendChild(wrapper);
    }

    async function fetchToken() {
        const body = new URLSearchParams({ room_name: roomName });
        const response = await fetch("/api/livekit/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: body.toString(),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Failed to get LiveKit token.");
        }
        return data;
    }

    async function joinRoom() {
        if (room) {
            return;
        }
        joinButton.disabled = true;
        statusNode.textContent = "Requesting LiveKit token...";

        try {
            const tokenData = await fetchToken();
            room = new livekit.Room();

            room.on(livekit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
                attachTrack(track, participant);
            });

            room.on(livekit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
                removeTrack(participant.identity, track.sid);
            });

            room.on(livekit.RoomEvent.LocalTrackPublished, (publication, participant) => {
                if (publication.track) {
                    attachTrack(publication.track, participant);
                }
            });

            room.on(livekit.RoomEvent.LocalTrackUnpublished, (publication, participant) => {
                if (publication.track) {
                    removeTrack(participant.identity, publication.track.sid);
                }
            });

            await room.connect(tokenData.server_url, tokenData.participant_token);
            await room.localParticipant.enableCameraAndMicrophone();
            statusNode.textContent = `Connected to ${roomName}.`;
            leaveButton.disabled = false;
            micButton.disabled = false;
            cameraButton.disabled = false;
            screenButton.disabled = false;
            renderPlaceholder();
        } catch (error) {
            statusNode.textContent = error.message || "Failed to connect to LiveKit.";
            joinButton.disabled = false;
        }
    }

    function leaveRoom() {
        if (!room) {
            return;
        }
        room.disconnect();
        room = null;
        grid.innerHTML = "";
        renderPlaceholder();
        joinButton.disabled = false;
        leaveButton.disabled = true;
        statusNode.textContent = "Disconnected from LiveKit room.";
    }

    async function toggleMicrophone() {
        if (!room) {
            return;
        }
        micEnabled = !micEnabled;
        await room.localParticipant.setMicrophoneEnabled(micEnabled);
        micButton.textContent = micEnabled ? "Mic" : "Mic off";
    }

    async function toggleCamera() {
        if (!room) {
            return;
        }
        cameraEnabled = !cameraEnabled;
        await room.localParticipant.setCameraEnabled(cameraEnabled);
        cameraButton.textContent = cameraEnabled ? "Camera" : "Camera off";
    }

    async function toggleScreenShare() {
        if (!room) {
            return;
        }
        screenEnabled = !screenEnabled;
        await room.localParticipant.setScreenShareEnabled(screenEnabled);
        screenButton.textContent = screenEnabled ? "Stop sharing" : "Share screen";
    }

    joinButton.addEventListener("click", joinRoom);
    leaveButton.addEventListener("click", leaveRoom);
    micButton.addEventListener("click", toggleMicrophone);
    cameraButton.addEventListener("click", toggleCamera);
    screenButton.addEventListener("click", toggleScreenShare);
    leaveButton.disabled = true;
    micButton.disabled = true;
    cameraButton.disabled = true;
    screenButton.disabled = true;
})();
