importScripts('lib/ExtPay.js');

const extpay = ExtPay('poliscan')
extpay.startBackground();

let user = {};
extpay.onPaid.addListener(currentUser => {
    user = currentUser;
    console.log(user);
})
extpay.getUser().then(currentUser => {
    user = currentUser;
})


let newsSites = [
    "newsweek.com",
    "foxnews.com",
    "cnn.com",
    "nytimes.com",
    "washingtonpost.com",
    "bbc.com",
    "reuters.com",
    "apnews.com",
    "npr.org"
];

const isNewsSite = (url) => {
    return newsSites.some(site => url.includes(site));
};

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

async function fetchWithRetry(url, options, retries = MAX_RETRIES) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response;
    } catch (error) {
        if (retries > 0) {
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
            return fetchWithRetry(url, options, retries - 1);
        }
        throw error;
    }
}

async function analyzeArticle(url, text) {
    try {
        const formData = new FormData();
        formData.append("url", url);
        if (text) formData.append("text", text);

        const endpoint = url.startsWith("https://www.youtube.com/watch") 
            ? "https://poltiscan-service-1092122045742.us-central1.run.app/generate_report_from_youtube"
            : "https://poltiscan-service-1092122045742.us-central1.run.app/generate_report";

        const response = await fetchWithRetry(endpoint, {
            method: "POST",
            body: formData
        });

        const analysis = await response.json();
        if (!analysis) throw new Error("No analysis data received");

        // Add expiration timestamp (24 hours from now)
        const storageData = {
            data: analysis,
            expires: Date.now() + (24 * 60 * 60 * 1000)
        };

        await chrome.storage.local.set({ [url]: storageData });
        return analysis;
    } catch (error) {
        console.error("Analysis failed:", error);
        return null;
    }
}

// Listen for tab updates
chrome.tabs.onActivated.addListener(async (tabId, changeInfo, tab) => {
    if (!tabId || !changeInfo || !tab) {
        return;
    }

    // Reset chat for new tab
    setupNewChat(await getCurrentTab());

    if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
        if (!isNewsSite(tab.url)) return;
        await analyzeArticle(tab.url, "");
    }
});

// // Also listen for tab updates to handle page refreshes
// chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
//     console.log(tab);
//     if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
//         if (!isNewsSite(tab.url)) return;
//         // Reset chat for updated tab
//         setupNewChat(await getCurrentTab());
//     }
// });

chrome.runtime.onInstalled.addListener(async () => {
	chrome.contextMenus.create({
		id: "analyze",
		title: "Analyze Article",
		type: 'normal',
        contexts: ["selection", "page"]
	});
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    let url = tab.url;
    let tabId = tab.id;

    let jsonResult = undefined;

    if (url.startsWith("https://www.youtube.com/watch") && !info.selectionText) {
        const formData = new FormData();
        formData.append("url", url);

        jsonResult = await fetch("https://poltiscan-service-1092122045742.us-central1.run.app/generate_report_from_youtube", {
            method: "POST",
            body: formData,
        }).catch((err) => {
            return null;
        });
    } else {
        let text = info.selectionText || "";
        
        const formData = new FormData();
        formData.append("url", url);
        formData.append("text", text);

        jsonResult = await fetch("https://poltiscan-service-1092122045742.us-central1.run.app/generate_report", {
            method: "POST",
            body: formData,
        }).catch((err) => {
            return null;
        });
    }

    const analysis = await jsonResult.json();

    if (analysis == undefined || analysis == null) {
        return;
    }

    // Add expiration timestamp (24 hours from now)
    const storageData = {
        data: analysis,
        expires: Date.now() + (24 * 60 * 60 * 1000)
    };

    chrome.storage.local.set({ [url]: storageData });
});

async function getCurrentTab() {
    let queryOptions = { active: true, lastFocusedWindow: true };
    let [tab] = await chrome.tabs.query(queryOptions);
    if (!tab) {
        // If no active tab found, try getting the current tab
        [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    }
    return tab;
}


/* CHAT FEATURE */
let webSocket = null;
let chatHistory = [];
let currentSequence = 0;
let currentChatId = null;

function connect() {
    console.log("connect")
    webSocket = new WebSocket('wss://poltiscan-service-1092122045742.us-central1.run.app/chat');
    chatHistory = [];
    currentSequence = 0;

    webSocket.onopen = async (event) => {
        console.log('chat websocket open');
        keepAlive();

        let tab = await getCurrentTab();
        console.log('Current tab:', tab); // Debug log
        
        if (tab && tab.url && !tab.url.startsWith('chrome://')) {
            console.log('Sending URL:', tab.url); // Debug log
            let data = {
                type: 'new_article',
                sequence: currentSequence,
                data: tab.url,
                email: user.email || 'anonymous'  // Include user email from ExtPay
            }
            webSocket.send(JSON.stringify(data));
        } else {
            console.log('Invalid tab or URL:', tab); // Debug log
        }
    };

    webSocket.onmessage = (event) => {
        console.log(`websocket received message: ${event.data}`);

        try {
            const message = JSON.parse(event.data);
            console.log(message);
            
            // Handle different message types
            switch (message.type) {
                case 'history':
                    if (message.chat_id !== currentChatId) {
                        currentChatId = message.chat_id;
                        chatHistory = message.data.messages;
                    }
                    break;
                    
                case 'message':
                    if (message.chat_id === currentChatId && message.sequence >= currentSequence) {
                        currentSequence = message.sequence;
                        chatHistory.push({
                            message: message.data.message,
                            role: message.data.role
                        });
                    }
                    break;
                    
                case 'error':
                    console.error('WebSocket error:', message.data.error);
                    break;
            }

            // Send updated chat history to popup
            chrome.runtime.sendMessage({
                action: "chat_history_update", 
                data: chatHistory
            });
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    };

    webSocket.onclose = (event) => {
        console.log('websocket connection closed');
        webSocket = null;
        currentChatId = null;
        currentSequence = 0;
        connect();
    };
}

function keepAlive() {
    const keepAliveIntervalId = setInterval(
        () => {
            if (webSocket) {
                webSocket.send('keepalive');
            } else {
                clearInterval(keepAliveIntervalId);
            }
        },
        20 * 1000 
    );
}

function disconnect() {
    console.log("disconnect");
    if (webSocket == null) {
        return;
    }
    webSocket.close();
    console.log("closed");
}

chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
    if (request.action === 'sendChatMessage') {
        if (webSocket != null) {
            currentSequence++;
            const message = {
                type: 'message',
                sequence: currentSequence,
                data: request.message
            };
            
            chatHistory.push({
                message: request.message,
                role: "user"
            });
            
            chrome.runtime.sendMessage({
                action: "chat_history_update", 
                data: chatHistory
            });
            
            webSocket.send(JSON.stringify(message));
        }
        return true;
    }
    if (request.action === 'popup_opened') {
        chrome.runtime.sendMessage({
            action: "chat_history_update", 
            data: chatHistory
        });
        return true;
    }
    return false;
});

const setupNewChat = async (tab) => {
    if (webSocket) {
        // Reset sequence ID for new article
        currentSequence = 0;
        let u = await extpay.getUser();
        const message = {
            type: 'new_article',
            sequence: currentSßequence,
            data: tab.url,
            email: u.email || 'anonymous'  // anonymous shouldn't happenß
        };
        
        console.log(message);

        webSocket.send(JSON.stringify(message));
        chatHistory = [];
    } else {
        // If websocket is not connected, reconnect
        connect();
    }
};

connect();