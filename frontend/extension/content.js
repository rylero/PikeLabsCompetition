let chatContainer = undefined;
let chatOpen = false;

let messageContainer = undefined;
let inputBox = undefined;
let submitButton = undefined;

let email = "leroy.ryan09@gmail.com";
let url = window.location.href;

const buttonSubmit = () => {
    const ws = new WebSocket("ws://192.168.1.20:34052");

    ws.send({
        inital
    })
}

const createChatIcon = () => {
    const icon = document.createElement("img");
    icon.src = chrome.runtime.getURL("./chaticon.svg");
    icon.className = "politiscan-chat-icon";

    chatContainer = document.createElement("div");
    chatContainer.style.display = chatOpen ? 'flex' : 'none';
    chatContainer.className = "politiscan-chat-container";

    /* Input container */
    let inputContainer = document.createElement("div");
    inputContainer.className = "inputContainer";

    inputBox = document.createElement("textarea");
    submitButton = document.createElement("button");
    submitButton.textContent = "Submit";
    submitButton.addEventListener("click", () => buttonSubmit());

    inputContainer.appendChild(inputBox);
    inputContainer.appendChild(submitButton);

    /* Message container */
    messageContainer = document.createElement("div");
    messageContainer.className = "messageContainer";

    chatContainer.appendChild(messageContainer);
    chatContainer.appendChild(inputContainer);


    icon.addEventListener("click", () => {
        chatOpen = !chatOpen;
        chatContainer.style.display = chatOpen ? 'flex' : 'none';
    });
    
    document.body.appendChild(chatContainer);
    document.body.appendChild(icon);
}

window.onload = () => {
    createChatIcon();
}