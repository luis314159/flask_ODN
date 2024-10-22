document.getElementById('send-btn').addEventListener('click', sendMessage);

document.getElementById('user-input').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const userInput = document.getElementById('user-input').value.trim();
    if (userInput === "") return;

    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<p class="user-message"><strong>You:</strong> ${userInput}</p>`;

    document.getElementById('user-input').value = '';

    const response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userInput })
    });

    const data = await response.json();
    if (data.response) {
        chatBox.innerHTML += `<p class="assistant-message"><strong>Visteon Assistant:</strong> ${data.response}</p>`;
    } else {
        chatBox.innerHTML += `<p class="assistant-message"><strong>Error:</strong> Something went wrong.</p>`;
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}