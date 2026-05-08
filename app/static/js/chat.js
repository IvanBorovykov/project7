(function () {
    const script = document.currentScript;
    if (!script) {
        return;
    }

    const chatId = script.dataset.chatId;
    const stream = document.getElementById("chat-stream");
    if (!chatId || !stream) {
        return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${chatId}`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const card = document.createElement("article");
        card.className = "message-card";

        const head = document.createElement("div");
        head.className = "message-head";
        head.innerHTML = `<strong>${data.sender}</strong><span>${data.created_at}</span>`;
        card.appendChild(head);

        if (data.content) {
            const body = document.createElement("p");
            body.textContent = data.content;
            card.appendChild(body);
        }

        if (data.attachment_url) {
            const link = document.createElement("a");
            link.href = data.attachment_url;
            link.target = "_blank";
            link.className = "attachment-link";
            link.textContent = data.attachment_name;
            card.appendChild(link);
        }

        stream.appendChild(card);
        stream.scrollTop = stream.scrollHeight;
    };
})();
