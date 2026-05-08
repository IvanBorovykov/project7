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
        card.innerHTML = `<strong>${data.kind}</strong><span>${data.content}</span>`;
        container.prepend(card);
    };
})();
