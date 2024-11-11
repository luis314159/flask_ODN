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
        const formattedResponse = marked.parse(data.response);
        chatBox.innerHTML += `<p class="assistant-message"><strong>Visteon Assistant:</strong> ${formattedResponse}</p>`;
    } else {
        chatBox.innerHTML += `<p class="assistant-message"><strong>Error:</strong> Something went wrong.</p>`;
    }
    chatBox.scrollTop = chatBox.scrollHeight;

    // Ocultar preguntas después de enviar un mensaje
    hideQuestionsCompletely();
}

document.addEventListener('DOMContentLoaded', async () => {
    const response = await fetch('/get_default_questions');
    const questions = await response.json();
    const questionsList = document.getElementById('questions-list');
    const chatContainer = document.querySelector('.chat-container');

    questions.forEach(question => {
        const button = document.createElement('button');
        button.textContent = question;
        button.onclick = () => {
            document.getElementById('user-input').value = question;
            sendMessage();
            hideQuestionsCompletely();
        };
        questionsList.appendChild(button);
    });

    chatContainer.classList.add('collapsed'); // Tamaño inicial del área de chat
});

function hideQuestionsCompletely() {
    const questionsContainer = document.querySelector('.questions-container');
    const chatContainer = document.querySelector('.chat-container');

    questionsContainer.classList.add('hidden');
    chatContainer.classList.add('intermediate');
    chatContainer.classList.remove('collapsed');
    chatContainer.classList.remove('expanded');
}

function toggleQuestions() {
    const questionsContainer = document.querySelector('.questions-container');
    const chatContainer = document.querySelector('.chat-container');
    const toggleButton = document.querySelector('.toggle-visibility');

    if (questionsContainer.classList.contains('minimized')) {
        questionsContainer.classList.remove('minimized');
        questionsContainer.style.display = 'block'; // Mostrar
        chatContainer.classList.add('collapsed');
        chatContainer.classList.remove('expanded');
        toggleButton.textContent = '▼';
    } else {
        questionsContainer.classList.add('minimized');
        questionsContainer.style.display = 'block';
        chatContainer.classList.add('expanded');
        chatContainer.classList.remove('collapsed');
        toggleButton.textContent = '▲';
    }
}

//
// document.getElementById('user-input').addEventListener('input', () => {
//     const questionsContainer = document.querySelector('.questions-container');
//     if (!questionsContainer.classList.contains('hidden')) {
//         hideQuestionsCompletely();
//     }
// });