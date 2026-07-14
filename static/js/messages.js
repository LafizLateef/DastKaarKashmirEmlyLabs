// ===============================
// DASTKAAR MESSAGES — SEND & SWITCH CONVERSATION
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    const sendBtn = document.getElementById("send-btn");
    const input = document.getElementById("message-input");

    if (sendBtn && input) {
        sendBtn.addEventListener("click", sendMessage);
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    document.querySelectorAll("#chat-list-items .chat-list-item").forEach((item) => {
        item.addEventListener("click", () => {
            const contact = item.dataset.contact;
            if (!contact) return;
            window.location.href = `/messages?contact=${encodeURIComponent(contact)}`;
        });
    });

    scrollChatToBottom();

});

function scrollChatToBottom() {
    const chat = document.getElementById("chat-messages");
    if (chat) chat.scrollTop = chat.scrollHeight;
}

function formatTime(date) {
    let hours = date.getHours();
    const minutes = date.getMinutes().toString().padStart(2, "0");
    const period = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    return `${hours}:${minutes} ${period}`;
}

function appendMessageBubble(text, time) {

    const chat = document.getElementById("chat-messages");
    if (!chat) return null;

    const emptyState = chat.querySelector(".empty-state");
    if (emptyState) emptyState.remove();

    const row = document.createElement("div");
    row.className = "message-row sent";

    const wrapper = document.createElement("div");

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = text;

    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = time;

    wrapper.append(bubble, meta);
    row.append(wrapper);
    chat.append(row);

    scrollChatToBottom();

    return row;

}

async function sendMessage() {

    const input = document.getElementById("message-input");
    const chat = document.getElementById("chat-messages");
    const sendBtn = document.getElementById("send-btn");

    if (!input || !chat) return;

    const text = input.value.trim();
    if (!text) return;

    const contact = chat.dataset.activeContact;

    input.value = "";
    sendBtn.disabled = true;

    const optimisticRow = appendMessageBubble(text, formatTime(new Date()));

    try {

        const res = await fetch(`/api/messages/${encodeURIComponent(contact)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const data = await res.json();

        if (!data.success) {
            if (optimisticRow) optimisticRow.remove();
            alert(data.message || "Could not send message.");
            input.value = text;
        }

    } catch (err) {
        console.error(err);
        if (optimisticRow) optimisticRow.remove();
        alert("Could not send message. Please try again.");
        input.value = text;
    } finally {
        sendBtn.disabled = false;
    }

}
