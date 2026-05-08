(function () {
    const script = document.currentScript;
    const container = document.getElementById("notification-list");
    if (!script || !container) {
        return;
    }

    const userId = script.dataset.userId;
    if (!userId) {
        return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/notifications/${userId}`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const card = document.createElement("div");
        card.className = "notice-card";

        const title = document.createElement("strong");
        title.textContent = data.kind || "notification";
        card.appendChild(title);

        const content = document.createElement("span");
        content.textContent = data.content || "";
        card.appendChild(content);

        container.prepend(card);
    };
})();
