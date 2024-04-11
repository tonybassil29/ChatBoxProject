// chat.js
document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');

    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();

        let userMessage = chatInput.value.trim();
        if(userMessage === "") return; // Do nothing if the message is empty

        // Append the user's message to the chat box
        let userDiv = document.createElement('div');
        userDiv.className = 'message user-message';
        userDiv.textContent = userMessage;
        chatBox.appendChild(userDiv);

        // Clear the input field and maintain focus
        chatInput.value = '';
        chatInput.focus();

        // Send the message to the server
        fetch('/chris', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            // Append the chatbot's response to the chat box
            let botDiv = document.createElement('div');
            botDiv.className = 'message bot-message';
            botDiv.textContent = data.response;
            chatBox.appendChild(botDiv);

            // Auto-scroll to the latest message
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
            let errorDiv = document.createElement('div');
            errorDiv.className = 'message error-message';
            errorDiv.textContent = 'Error: Could not reach the chatbot.';
            chatBox.appendChild(errorDiv);
        });
    });
});