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


// Function to collect article text
async function collectArticleText(tabId) {
    try {
        const result = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: function() {
                try {
                    // const article = document.querySelector('main,article');
                    // if (article) {
                    return Array.from(document.querySelectorAll('p,article>div')).map(p => p.innerText).join('\n\n');
                    // }
                    // return null;
                } catch (err) {
                    console.error('Error in content script:', err);
                    return null;
                }
            }
        });

        if (result && result.length > 0 && result[0].result) {
            await chrome.storage.local.set({ [`article_${tabId}`]: result[0].result });
            return result[0].result;
        }
        return null;
    } catch (err) {
        console.error('Failed to collect article text:', err);
        return null;
    }
}

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

        return analysis;
    } catch (error) {
        console.error("Analysis failed:", error);
        return null;
    }
}

// Listen for tab updates
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
        const text = await collectArticleText(tabId);
        if (!text || !isNewsSite(tab.url)) return;

        const analysis = await analyzeArticle(tab.url, text);
        if (analysis) {
            chrome.storage.local.set({ [`analysis_${tabId}`]: analysis });
        }
    }
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
    if (request.action === 'getArticleText') {
        collectArticleText(request.tabId).then(text => {
            sendResponse({ text: text });
        });
        return true; // Required for async response
    }
    return false; // Return false if not handling the message
});

chrome.runtime.onInstalled.addListener(async () => {
	chrome.contextMenus.create({
		id: "analyze",
		title: "Analyze Article",
		type: 'normal',
        contexts: ["selection", "page"]
	});
});

chrome.contextMenus.onClicked.addListener(async (item, tab) => {
    let url = tab.url;
    let tabId = tab.id;

    let jsonResult = undefined;

    if (url.startsWith("https://www.youtube.com/watch") && !item.selectionText) {
        const formData = new FormData();
        formData.append("url", url);

        jsonResult = await fetch("https://poltiscan-service-1092122045742.us-central1.run.app/generate_report_from_youtube", {
            method: "POST",
            body: formData,
        }).catch((err) => {
            return null;
        });
    } else {
        let text = info.selectionText;
        if (!text) {
            text = collectArticleText(tab.id);
        }
        
        if (!text) {
            returen;
        }

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

    chrome.storage.local.set({ [`analysis_${tabId}`]: analysis });
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
  webSocket = new WebSocket('wss://poltiscan-service-1092122045742.us-central1.run.app/chat');
  chatHistory = [];

  webSocket.onopen = async (event) => {
    console.log('chat websocket open');
    keepAlive();

    let tab = await getCurrentTab();
    let content = await collectArticleText(tab.id);

    let data = {
        url: tab.url,
        text: content
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