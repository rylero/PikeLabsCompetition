importScripts('lib/ExtPay.js');

const extpay = ExtPay('poliscan')
extpay.startBackground();

let user = {};
extpay.onPaid.addListener(currentUser => {
    user = currentUser;
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
            ? "http://0.0.0.0:8000/generate_report_from_youtube"
            : "http://0.0.0.0:8000/generate_report";

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
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
        if (!isNewsSite(tab.url)) return;

        const analysis = await analyzeArticle(tab.url, "");
        if (analysis) {
            // Storage is now handled in analyzeArticle
        }
    }
});

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

        jsonResult = await fetch("http://0.0.0.0:8000/generate_report_from_youtube", {
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

        jsonResult = await fetch("http://0.0.0.0:8000/generate_report", {
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
    // `tab` will either be a `tabs.Tab` instance or `undefined`.
    let [tab] = await chrome.tabs.query(queryOptions);
    return tab;
}


/* CHAT FEATURE */
let webSocket = null;
let chatHistory = [];

function connect() {
    console.log("connect")
  webSocket = new WebSocket('ws://0.0.0.0:8000/chat');
  chatHistory = [];

  webSocket.onopen = async (event) => {
    console.log('chat websocket open');
    keepAlive();

    let tab = await getCurrentTab();
    let data = {
        url: tab.url,
        text: ""
    }
    webSocket.send(JSON.stringify(data));
  };

  webSocket.onmessage = (event) => {
    console.log(`websocket received message: ${event.data}`);
    chatHistory.push({
        message: event.data,
        role: "system"
    });

    chrome.runtime.sendMessage({
        action: "chat_history_update", 
        data: chatHistory
    });
  };

  webSocket.onclose = (event) => {
    console.log('websocket connection closed');
    webSocket = null;
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
      // Set the interval to 20 seconds to prevent the service worker from becoming inactive.
      20 * 1000 
    );
  }

function disconnect() {
    console.log("disconnect");
  if (webSocket == null) {
    return;
  }
  webSocket.close();
  console.log("closed")
}

chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
    if (request.action === 'sendChatMessage') {
        if (webSocket != null) {
            chatHistory.push({
                message: request.message,
                role: "user"
            });
            chrome.runtime.sendMessage({
                action: "chat_history_update", 
                data: chatHistory
            });
            webSocket.send(request.message);
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

chrome.tabs.onActivated.addListener(async (tabId, changeInfo, tab) => {
    disconnect(); // disconnect for old tab
    connect(); // conncet for new tab
});

chrome.runtime.onSuspend.addListener(() => {
    disconnect(); // disconnect from websockets on service worker close    
});