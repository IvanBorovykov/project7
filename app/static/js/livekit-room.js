(function () {
    const script = document.currentScript;
    const statusNode = document.getElementById("livekit-status");
    const grid = document.getElementById("video-grid");
    const joinButton = document.getElementById("join-room-btn");
    const leaveButton = document.getElementById("leave-room-btn");
    const micButton = document.getElementById("toggle-mic-btn");
    const cameraButton = document.getElementById("toggle-camera-btn");
    const screenButton = document.getElementById("toggle-screen-btn");
    const startRecordingButton = document.getElementById("start-recording-btn");
    const stopRecordingButton = document.getElementById("stop-recording-btn");
    const recordingStatusNode = document.getElementById("recording-status");

    if (!script || !statusNode || !grid || !joinButton || !leaveButton || !micButton || !cameraButton || !screenButton) {
        return;
    }

    const meetingId = script.dataset.meetingId;
    const roomName = script.dataset.roomName;
    const configured = script.dataset.configured === "true";
    const recordingEnabled = script.dataset.recordingEnabled === "true";
    const canRecord = script.dataset.canRecord === "true";
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!configured) {
        joinButton.disabled = true;
        micButton.disabled = true;
        cameraButton.disabled = true;
        screenButton.disabled = true;
        leaveButton.disabled = true;
        if (startRecordingButton) {
            startRecordingButton.disabled = true;
        }
        if (stopRecordingButton) {
            stopRecordingButton.disabled = true;
        }
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
    let mediaRecorder = null;
    let recordingChunks = [];
    let recordingMimeType = "";
    let recordingCanvas = null;
    let recordingContext = null;
    let recordingAnimationFrame = null;
    let recordingAudioContext = null;
    let recordingAudioDestination = null;
    let recordingAudioSources = new Map();
    let recordingStream = null;

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
        updateRecordingControls(isConnected);
    }

    function updateRecordingControls(isConnected) {
        if (!startRecordingButton || !stopRecordingButton) {
            return;
        }
        const allowRecording = isConnected && recordingEnabled && canRecord;
        startRecordingButton.disabled = !allowRecording || Boolean(mediaRecorder);
        stopRecordingButton.disabled = !mediaRecorder;
    }

    function setRecordingStatus(message) {
        if (recordingStatusNode) {
            recordingStatusNode.textContent = message;
        }
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
        if (mediaRecorder) {
            mediaRecorder.stop();
        }
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

    function getSupportedRecordingMimeType() {
        const mimeTypes = [
            "video/webm;codecs=vp9,opus",
            "video/webm;codecs=vp8,opus",
            "video/webm",
        ];
        return mimeTypes.find((mimeType) => window.MediaRecorder && MediaRecorder.isTypeSupported(mimeType)) || "";
    }

    function cleanupRecordingResources() {
        if (recordingAnimationFrame) {
            cancelAnimationFrame(recordingAnimationFrame);
            recordingAnimationFrame = null;
        }
        recordingAudioSources.forEach((source) => source.disconnect());
        recordingAudioSources.clear();
        if (recordingAudioContext) {
            recordingAudioContext.close();
            recordingAudioContext = null;
        }
        recordingAudioDestination = null;
        if (recordingStream) {
            recordingStream.getTracks().forEach((track) => track.stop());
            recordingStream = null;
        }
        recordingCanvas = null;
        recordingContext = null;
    }

    function drawRecordingFrame() {
        if (!recordingCanvas || !recordingContext) {
            return;
        }
        const ctx = recordingContext;
        const width = recordingCanvas.width;
        const height = recordingCanvas.height;
        ctx.fillStyle = "#0f1720";
        ctx.fillRect(0, 0, width, height);

        const mediaTiles = Array.from(grid.querySelectorAll(".participant-tile"));
        const columns = Math.max(1, Math.ceil(Math.sqrt(mediaTiles.length || 1)));
        const rows = Math.max(1, Math.ceil((mediaTiles.length || 1) / columns));
        const gap = 24;
        const tileWidth = (width - gap * (columns + 1)) / columns;
        const tileHeight = (height - gap * (rows + 1)) / rows;

        if (!mediaTiles.length) {
            ctx.fillStyle = "#f3f4f6";
            ctx.font = "32px sans-serif";
            ctx.fillText("Waiting for participants...", 60, height / 2);
        }

        mediaTiles.forEach((tile, index) => {
            const column = index % columns;
            const row = Math.floor(index / columns);
            const x = gap + column * (tileWidth + gap);
            const y = gap + row * (tileHeight + gap);
            const video = tile.querySelector("video");
            const label = tile.querySelector(".participant-label");

            ctx.fillStyle = "#1f2937";
            ctx.fillRect(x, y, tileWidth, tileHeight);

            if (video && video.readyState >= 2) {
                ctx.drawImage(video, x, y, tileWidth, tileHeight);
            } else {
                ctx.fillStyle = "#d1d5db";
                ctx.font = "24px sans-serif";
                ctx.fillText("No video", x + 24, y + tileHeight / 2);
            }

            ctx.fillStyle = "rgba(15, 23, 32, 0.8)";
            ctx.fillRect(x, y + tileHeight - 52, tileWidth, 52);
            ctx.fillStyle = "#ffffff";
            ctx.font = "20px sans-serif";
            ctx.fillText(label ? label.textContent || "Participant" : "Participant", x + 16, y + tileHeight - 18);
        });

        recordingAnimationFrame = requestAnimationFrame(drawRecordingFrame);
    }

    function getAllPublishedTracks() {
        if (!room) {
            return [];
        }

        const publications = [];
        room.localParticipant.trackPublications.forEach((publication) => {
            publications.push(publication);
        });
        room.remoteParticipants.forEach((participant) => {
            participant.trackPublications.forEach((publication) => {
                publications.push(publication);
            });
        });
        return publications;
    }

    function addAudioTrackToRecording(track) {
        const mediaStreamTrack = track?.mediaStreamTrack;
        if (!recordingAudioContext || !recordingAudioDestination || !mediaStreamTrack || !isAudioTrack(track)) {
            return;
        }
        if (recordingAudioSources.has(mediaStreamTrack.id)) {
            return;
        }
        const sourceStream = new MediaStream([mediaStreamTrack]);
        const sourceNode = recordingAudioContext.createMediaStreamSource(sourceStream);
        sourceNode.connect(recordingAudioDestination);
        recordingAudioSources.set(mediaStreamTrack.id, sourceNode);
    }

    function removeAudioTrackFromRecording(track) {
        const mediaStreamTrack = track?.mediaStreamTrack;
        if (!mediaStreamTrack) {
            return;
        }
        const sourceNode = recordingAudioSources.get(mediaStreamTrack.id);
        if (!sourceNode) {
            return;
        }
        sourceNode.disconnect();
        recordingAudioSources.delete(mediaStreamTrack.id);
    }

    function buildRecordingStream() {
        recordingCanvas = document.createElement("canvas");
        recordingCanvas.width = 1280;
        recordingCanvas.height = 720;
        recordingContext = recordingCanvas.getContext("2d");
        drawRecordingFrame();

        const canvasStream = recordingCanvas.captureStream(20);
        if (!AudioContextClass) {
            throw new Error("This browser cannot mix meeting audio for recording.");
        }
        recordingAudioContext = new AudioContextClass();
        recordingAudioDestination = recordingAudioContext.createMediaStreamDestination();
        recordingAudioSources = new Map();

        getAllPublishedTracks().forEach((publication) => {
            addAudioTrackToRecording(publication.track);
        });

        recordingStream = new MediaStream([
            ...canvasStream.getVideoTracks(),
            ...recordingAudioDestination.stream.getAudioTracks(),
        ]);
        return recordingStream;
    }

    async function uploadRecording(blob) {
        const extension = recordingMimeType.includes("mp4") ? "mp4" : "webm";
        const formData = new FormData();
        formData.append("status", "available");
        formData.append("recording", new File([blob], `meeting-${meetingId}-recording.${extension}`, { type: blob.type }));

        const response = await fetch(`/api/meetings/${meetingId}/recording`, {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Failed to upload recording.");
        }
        if (data.recording_url) {
            const linkNode = document.getElementById("recording-link");
            if (linkNode) {
                linkNode.href = data.recording_url;
                linkNode.hidden = false;
            } else {
                const container = document.createElement("p");
                const link = document.createElement("a");
                link.id = "recording-link";
                link.href = data.recording_url;
                link.target = "_blank";
                link.textContent = "Open recording";
                container.appendChild(link);
                const panel = recordingStatusNode?.parentElement;
                if (panel) {
                    panel.appendChild(container);
                }
            }
        }
    }

    async function startRecording() {
        if (!room || mediaRecorder || !recordingEnabled || !canRecord) {
            return;
        }
        if (!window.MediaRecorder) {
            setRecordingStatus("MediaRecorder is not supported in this browser.");
            return;
        }

        recordingMimeType = getSupportedRecordingMimeType();
        if (!recordingMimeType) {
            setRecordingStatus("This browser cannot record the meeting stream.");
            return;
        }

        try {
            const stream = buildRecordingStream();
            recordingChunks = [];
            mediaRecorder = new MediaRecorder(stream, { mimeType: recordingMimeType });
            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    recordingChunks.push(event.data);
                }
            };
            mediaRecorder.onstop = async () => {
                const blob = new Blob(recordingChunks, { type: recordingMimeType });
                cleanupRecordingResources();
                mediaRecorder = null;
                updateRecordingControls(Boolean(room));

                if (!blob.size) {
                    setRecordingStatus("Recording stopped, but the file is empty.");
                    return;
                }

                setRecordingStatus("Uploading recording to server...");
                try {
                    await uploadRecording(blob);
                    setRecordingStatus("Recording saved on the server.");
                } catch (error) {
                    setRecordingStatus(error.message || "Failed to upload recording.");
                }
            };
            mediaRecorder.start(1000);
            setRecordingStatus("Recording in progress...");
            updateRecordingControls(true);
        } catch (error) {
            cleanupRecordingResources();
            mediaRecorder = null;
            updateRecordingControls(Boolean(room));
            setRecordingStatus(error.message || "Failed to start recording.");
        }
    }

    function stopRecording() {
        if (!mediaRecorder) {
            return;
        }
        setRecordingStatus("Stopping recording...");
        mediaRecorder.stop();
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
                if (mediaRecorder) {
                    addAudioTrackToRecording(track);
                }
            });

            room.on(livekit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
                removeTrack(participant, publication, track);
                if (mediaRecorder) {
                    removeAudioTrackFromRecording(track);
                }
            });

            room.on(livekit.RoomEvent.LocalTrackPublished, (publication, participant) => {
                if (publication.track) {
                    attachTrack(publication.track, publication, participant, { isLocal: true });
                    if (mediaRecorder) {
                        addAudioTrackToRecording(publication.track);
                    }
                }
            });

            room.on(livekit.RoomEvent.LocalTrackUnpublished, (publication, participant) => {
                if (publication.track) {
                    removeTrack(participant, publication, publication.track);
                    if (mediaRecorder) {
                        removeAudioTrackFromRecording(publication.track);
                    }
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
        if (mediaRecorder) {
            stopRecording();
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
    if (startRecordingButton) {
        startRecordingButton.addEventListener("click", startRecording);
    }
    if (stopRecordingButton) {
        stopRecordingButton.addEventListener("click", stopRecording);
    }
    setConnectedControls(false);
})();
