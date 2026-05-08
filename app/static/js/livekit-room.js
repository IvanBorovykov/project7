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

    const audioOutput = document.createElement("div");
    audioOutput.className = "livekit-audio-output";
    audioOutput.setAttribute("aria-hidden", "true");
    document.body.appendChild(audioOutput);

    let room = null;
    let micEnabled = true;
    let cameraEnabled = true;
    let screenEnabled = false;

    function isAudioTrack(track) {
        return track.kind === "audio" || track.kind === livekit.Track?.Kind?.Audio;
    }

    function isVideoTrack(track) {
        return track.kind === "video" || track.kind === livekit.Track?.Kind?.Video;
    }

    function trackKey(participant, publication, track) {
        const trackId = publication?.trackSid || track?.sid || track?.mediaStreamTrack?.id || publication?.source || "track";
        return `${participant.identity}-${trackId}`.replace(/[^a-zA-Z0-9_-]/g, "_");
    }

    function setConnectedControls(isConnected) {
        joinButton.disabled = isConnected;
        leaveButton.disabled = !isConnected;
        micButton.disabled = !isConnected;
        cameraButton.disabled = !isConnected;
        screenButton.disabled = !isConnected;
    }

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

    function tileId(participant, publication, track) {
        return `tile-${trackKey(participant, publication, track)}`;
    }

    function audioId(participant, publication, track) {
        return `audio-${trackKey(participant, publication, track)}`;
    }

    function detachTrack(track) {
        if (!track || typeof track.detach !== "function") {
            return;
        }
        track.detach().forEach((element) => element.remove());
    }

    function removeTrack(participant, publication, track) {
        const existing = document.getElementById(tileId(participant, publication, track));
        if (existing) {
            existing.remove();
        }
        const audio = document.getElementById(audioId(participant, publication, track));
        if (audio) {
            audio.remove();
        }
        detachTrack(track);
        renderPlaceholder();
    }

    function attachVideoTrack(track, publication, participant, isLocal) {
        clearPlaceholder();
        const wrapper = document.createElement("div");
        wrapper.className = "participant-tile";
        wrapper.id = tileId(participant, publication, track);

        const label = document.createElement("div");
        label.className = "participant-label";
        label.textContent = `${participant.name || participant.identity}${isLocal ? " (you)" : ""}`;
        wrapper.appendChild(label);

        const element = track.attach();
        element.classList.add("participant-media");
        element.autoplay = true;
        element.playsInline = true;
        element.muted = isLocal;
        wrapper.appendChild(element);
        grid.appendChild(wrapper);
    }

    function attachAudioTrack(track, publication, participant) {
        const element = track.attach();
        element.id = audioId(participant, publication, track);
        element.autoplay = true;
        element.hidden = true;
        audioOutput.appendChild(element);
    }

    function attachTrack(track, publication, participant, options = {}) {
        if (!track) {
            return;
        }
        removeTrack(participant, publication, track);
        if (options.isLocal && isAudioTrack(track)) {
            return;
        }
        if (isAudioTrack(track)) {
            attachAudioTrack(track, publication, participant);
            return;
        }
        if (isVideoTrack(track)) {
            attachVideoTrack(track, publication, participant, Boolean(options.isLocal));
        }
    }

    function resetRoomUi(message) {
        room = null;
        grid.innerHTML = "";
        audioOutput.innerHTML = "";
        micEnabled = true;
        cameraEnabled = true;
        screenEnabled = false;
        micButton.textContent = "Mic";
        cameraButton.textContent = "Camera";
        screenButton.textContent = "Share screen";
        setConnectedControls(false);
        statusNode.textContent = message;
        renderPlaceholder();
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
                attachTrack(track, publication, participant);
            });

            room.on(livekit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
                removeTrack(participant, publication, track);
            });

            room.on(livekit.RoomEvent.LocalTrackPublished, (publication, participant) => {
                if (publication.track) {
                    attachTrack(publication.track, publication, participant, { isLocal: true });
                }
            });

            room.on(livekit.RoomEvent.LocalTrackUnpublished, (publication, participant) => {
                if (publication.track) {
                    removeTrack(participant, publication, publication.track);
                }
            });

            room.on(livekit.RoomEvent.Disconnected, () => {
                resetRoomUi("Disconnected from LiveKit room.");
            });

            await room.connect(tokenData.server_url, tokenData.participant_token);
            await room.localParticipant.enableCameraAndMicrophone();
            statusNode.textContent = `Connected to ${roomName}.`;
            setConnectedControls(true);
            renderPlaceholder();
        } catch (error) {
            if (room) {
                room.disconnect();
                room = null;
            }
            statusNode.textContent = error.message || "Failed to connect to LiveKit.";
            setConnectedControls(false);
        }
    }

    function leaveRoom() {
        if (!room) {
            return;
        }
        room.disconnect();
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
    setConnectedControls(false);
})();
