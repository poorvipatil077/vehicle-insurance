console.log("Vehicle Insurance App loaded");

// Theme Toggle
const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        themeToggle.textContent = newTheme === 'dark' ? '☀️ Light' : '🌙 Dark';
    });
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);
if (themeToggle) {
    themeToggle.textContent = savedTheme === 'dark' ? '☀️ Light' : '🌙 Dark';
}

// AI Chatbot
const chatbotBtn = document.createElement('button');
chatbotBtn.id = 'chatbot-toggle';
chatbotBtn.textContent = '🤖 Help';
chatbotBtn.style.cssText = 'position:fixed; bottom:20px; right:20px; padding:10px 20px; border-radius:50px; background:#333; color:white; border:none; cursor:pointer; z-index:1000;';
document.body.appendChild(chatbotBtn);

const chatbotWindow = document.createElement('div');
chatbotWindow.id = 'chatbot-window';
chatbotWindow.style.cssText = 'display:none; position:fixed; bottom:80px; right:20px; width:300px; height:400px; background:var(--container-bg); border:1px solid var(--border-color); box-shadow:0 0 10px rgba(0,0,0,0.2); flex-direction:column; z-index:1000;';
chatbotWindow.innerHTML = `
    <div style="background:#333; color:white; padding:10px; display:flex; justify-content:space-between;">
        <span>AI Assistant</span>
        <button onclick="document.getElementById('chatbot-window').style.display='none'" style="background:none; border:none; color:white; cursor:pointer;">X</button>
    </div>
    <div id="chatbot-messages" style="flex:1; overflow-y:auto; padding:10px; font-size:14px;">
        <div style="margin-bottom:10px;">Hello! How can I help you today?</div>
    </div>
    <div style="padding:10px; border-top:1px solid var(--border-color); display:flex;">
        <input type="text" id="chatbot-input" style="flex:1; padding:5px; border:1px solid var(--border-color); background:var(--bg-color); color:var(--text-color);" placeholder="Type a message...">
        <button id="chatbot-send" style="padding:5px 10px; background:#333; color:white; border:none; cursor:pointer; margin-left:5px;">Send</button>
    </div>
`;
document.body.appendChild(chatbotWindow);

chatbotBtn.onclick = () => {
    chatbotWindow.style.display = chatbotWindow.style.display === 'none' ? 'flex' : 'none';
};

const chatbotInput = document.getElementById('chatbot-input');
const chatbotSend = document.getElementById('chatbot-send');
const chatbotMessages = document.getElementById('chatbot-messages');

function appendMessage(text, isUser = false) {
    const msg = document.createElement('div');
    msg.style.marginBottom = '10px';
    msg.style.textAlign = isUser ? 'right' : 'left';
    msg.style.color = isUser ? '#007bff' : 'inherit';
    msg.textContent = text;
    chatbotMessages.appendChild(msg);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

chatbotSend.onclick = () => {
    const text = chatbotInput.value.trim();
    if (text) {
        appendMessage(text, true);
        chatbotInput.value = '';
        
        // Simple AI Logic
        setTimeout(() => {
            let response = "I'm sorry, I don't understand. Can you rephrase?";
            if (text.toLowerCase().includes('claim')) response = "You can submit a claim through the Dashboard after logging in.";
            if (text.toLowerCase().includes('fraud')) response = "Our system uses AI to detect fraud with high accuracy.";
            if (text.toLowerCase().includes('hi') || text.toLowerCase().includes('hello')) response = "Hi there! How can I assist you with your insurance?";
            appendMessage(response);
        }, 500);
    }
};

chatbotInput.onkeypress = (e) => { if (e.key === 'Enter') chatbotSend.click(); };
