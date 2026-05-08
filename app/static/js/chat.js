(function () {
    const script = document.currentScript;
    if (!script) {
        return;
    }

    const chatId = script.dataset.chatId;
    const currentUserId = script.dataset.currentUserId;
    const stream = document.getElementById("chat-stream");
    const status = document.getElementById("chat-connection-status");
    const form = document.getElementById("chat-message-form");
    const textarea = document.getElementById("chat-message-input");
    const fileInput = document.getElementById("chat-attachment-input");
    const sendButton = document.getElementById("chat-send-btn");
    if (!chatId || !stream) {
        return;
    }

    function setStatus(label, className) {
        if (!status) {
            return;
        }
        status.textContent = label;
        status.className = `connection-status ${className}`;
    }

    function scrollToLatest() {
        stream.scrollTop = stream.scrollHeight;
    }

    function hasMessageBody() {
        const text = textarea ? textarea.value.trim() : "";
        const hasFile = fileInput && fileInput.files.length > 0;
        return Boolean(text || hasFile);
    }

    function updateSendState() {
        if (sendButton) {
            sendButton.disabled = !hasMessageBody();
        }
    }

    function appendText(parent, tagName, text, className) {
        const node = document.createElement(tagName);
        if (className) {
            node.className = className;
        }
        node.textContent = text;
        parent.appendChild(node);
        return node;
    }

    function appendMessage(data) {
        const emptyState = document.getElementById("empty-chat-state");
        if (emptyState) {
            emptyState.remove();
        }

        const card = document.createElement("article");
        card.className = "message-card";
        if (currentUserId && data.sender_id === currentUserId) {
            card.classList.add("message-card-own");
        }

        const head = document.createElement("div");
        head.className = "message-head";
        appendText(head, "strong", data.sender || "Unknown sender");
        appendText(head, "span", data.created_at || "");
        card.appendChild(head);

        if (data.content) {
            appendText(card, "p", data.content);
        }

        if (data.attachment_url) {
            const link = document.createElement("a");
            link.href = data.attachment_url;
            link.target = "_blank";
            link.rel = "noopener";
            link.className = "attachment-link";
            link.textContent = data.attachment_name || "Attachment";
            card.appendChild(link);
        }

        stream.appendChild(card);
        scrollToLatest();
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${chatId}`);

    socket.onopen = () => {
        setStatus("Live", "connection-status-live");
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        appendMessage(data);
    };

    socket.onclose = () => {
        setStatus("Offline", "connection-status-offline");
    };

    socket.onerror = () => {
        setStatus("Connection issue", "connection-status-offline");
    };

    if (form && textarea) {
        textarea.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                if (hasMessageBody()) {
                    form.requestSubmit();
                }
            }
        });

        form.addEventListener("submit", (event) => {
            if (!hasMessageBody()) {
                event.preventDefault();
                updateSendState();
                textarea.focus();
                return;
            }
            if (sendButton) {
                sendButton.disabled = true;
                sendButton.textContent = "Sending...";
            }
        });
    }

    if (textarea) {
        textarea.addEventListener("input", updateSendState);
    }
    if (fileInput) {
        fileInput.addEventListener("change", updateSendState);
    }

    scrollToLatest();
    updateSendState();
})();
