document.addEventListener("DOMContentLoaded", function () {
    const chatLauncher = document.getElementById("chatLauncher");
    const chatContainer = document.getElementById("chatContainer");
    const chatCloseBtn = document.getElementById("chatCloseBtn");
    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");
    const chatSendBtn = document.getElementById("chatSendBtn");
    const chatQuickStart = document.getElementById("chatQuickStart");

    let isSending = false;
    let sessionId = "shopzone_" + Date.now();

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function openChat() {
        chatContainer.classList.add("open");
        chatContainer.setAttribute("aria-hidden", "false");
        chatLauncher.setAttribute("aria-expanded", "true");
        chatInput.focus();
    }

    function closeChat() {
        chatContainer.classList.remove("open");
        chatContainer.setAttribute("aria-hidden", "true");
        chatLauncher.setAttribute("aria-expanded", "false");
    }

    function escapeHTML(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatMessage(text) {
        return escapeHTML(text).replace(/\n/g, "<br>");
    }

    function addMessage(text, sender) {
        // Remove existing welcome message if adding new one
        if (sender === "bot" && chatMessages.children.length === 1) {
            chatMessages.innerHTML = "";
        }

        const messageWrapper = document.createElement("div");
        messageWrapper.className = `message ${sender}`;

        const bubble = document.createElement("div");
        bubble.className = "message-content";
        bubble.innerHTML = formatMessage(text);

        messageWrapper.appendChild(bubble);
        chatMessages.appendChild(messageWrapper);
        scrollToBottom();
    }

    function addTypingIndicator() {
        removeTypingIndicator();

        const typingWrapper = document.createElement("div");
        typingWrapper.className = "message bot";
        typingWrapper.id = "typingIndicator";

        const bubble = document.createElement("div");
        bubble.className = "message-content typing-bubble";
        bubble.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;

        typingWrapper.appendChild(bubble);
        chatMessages.appendChild(typingWrapper);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const typing = document.getElementById("typingIndicator");
        if (typing) typing.remove();
    }

    function clearDynamicQuickReplies() {
        document.querySelectorAll(".dynamic-quick-replies").forEach((el) => el.remove());
    }

    function addQuickReplies(replies) {
        if (!replies || !replies.length) return;

        clearDynamicQuickReplies();

        const wrap = document.createElement("div");
        wrap.className = "chat-quick-replies dynamic-quick-replies";

        replies.forEach((item) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "quick-btn";
            btn.textContent = item.text || "Option";

            btn.addEventListener("click", function () {
                if (item.url) {
                    window.location.href = item.url;
                } else {
                    sendMessage(item.text);
                }
            });

            wrap.appendChild(btn);
        });

        chatMessages.appendChild(wrap);
        scrollToBottom();
    }

    function setSendingState(state) {
        isSending = state;
        chatInput.disabled = state;
        chatSendBtn.disabled = state;
        if (chatSendBtn) chatSendBtn.style.opacity = state ? "0.5" : "1";
    }

    async function sendMessage(customText = null) {
        if (isSending) return;

        const message = customText || chatInput.value.trim();
        if (!message) return;

        // Hide quick start when first message sent
        if (chatQuickStart) {
            chatQuickStart.style.display = "none";
        }

        clearDynamicQuickReplies();
        addMessage(message, "user");

        if (!customText) {
            chatInput.value = "";
        }

        setSendingState(true);
        addTypingIndicator();

        try {
            const csrftoken = getCookie("csrftoken");

            const response = await fetch("/store/chat/message/", {
                method: "POST",
                mode: "same-origin",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            const data = await response.json();
            removeTypingIndicator();

            if (response.ok && data.success) {
                addMessage(data.reply || "I'm here to help.", "bot");
                addQuickReplies(data.quick_replies || []);
            } else {
                addMessage(data.reply || "Sorry, I could not process your request.", "bot");
                addQuickReplies(data.quick_replies || []);
            }
        } catch (error) {
            console.error("Chat error:", error);
            removeTypingIndicator();
            addMessage("Sorry, the chatbot is temporarily unavailable. Please try again later.", "bot");
            addQuickReplies([
                { text: "Shipping and delivery" },
                { text: "Returns and refunds" },
                { text: "Payment methods" },
                { text: "Track my order" }
            ]);
        } finally {
            setSendingState(false);
            chatInput.focus();
            scrollToBottom();
        }
    }

    // Event Listeners
    if (chatLauncher) {
        chatLauncher.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (chatContainer.classList.contains("open")) {
                closeChat();
            } else {
                openChat();
            }
        });
    }

    if (chatCloseBtn) {
        chatCloseBtn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            closeChat();
        });
    }

    if (chatSendBtn) {
        chatSendBtn.addEventListener("click", function (e) {
            e.preventDefault();
            sendMessage();
        });
    }

    if (chatInput) {
        chatInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        // Focus on container open
        chatInput.addEventListener("blur", function () {
            setTimeout(() => chatInput.focus(), 100);
        });
    }

    if (chatQuickStart) {
        const quickButtons = chatQuickStart.querySelectorAll(".quick-btn");
        quickButtons.forEach((btn) => {
            btn.addEventListener("click", function (e) {
                e.preventDefault();
                const message = this.getAttribute("data-message");
                if (message) {
                    openChat();
                    sendMessage(message);
                }
            });
        });
    }

    // ESC to close
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && chatContainer.classList.contains("open")) {
            closeChat();
        }
    });
});