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

// Listen for tab updates
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
        let text = await collectArticleText(tabId);

        if (!text) {
            return;
        }

        let isNews = false;
        newsSites.forEach((a) => {
            if (tab.url.includes(a)) {
                isNews = true;
            }
        })
        if (isNews) {
            const formData = new FormData();
            formData.append("url", tab.url);
            formData.append("text", text);

            jsonResult = await fetch("http://0.0.0.0:8000/generate_report", {
                method: "POST",
                body: formData,
            }).catch((err) => {
                return null;
            });

            const analysis = await jsonResult.json();

            if (analysis == undefined || analysis == null) {
                return;
            }

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

        jsonResult = await fetch("http://0.0.0.0:8000/generate_report_from_youtube", {
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

        jsonResult = await fetch("http://0.0.0.0:8000/generate_report", {
            method: "POST",
            body: formData,
        }).catch((err) => {
            return null;
        });
    }

    const analysis = await jsonResult.json();
    console.log(analysis);

    if (analysis == undefined || analysis == null) {
        return;
    }

    chrome.storage.local.set({ [`analysis_${tabId}`]: analysis });
});



/* CHAT FEATURE */
// let webSocket = null;

// function connect() {
//   webSocket = new WebSocket('wss://example.com/ws');

//   webSocket.onopen = (event) => {
//     console.log('websocket open');
//     keepAlive();
//   };

//   webSocket.onmessage = (event) => {
//     console.log(`websocket received message: ${event.data}`);
//   };

//   webSocket.onclose = (event) => {
//     console.log('websocket connection closed');
//     webSocket = null;
//   };
// }

// function keepAlive() {
//     const keepAliveIntervalId = setInterval(
//       () => {
//         if (webSocket) {
//           webSocket.send('keepalive');
//         } else {
//           clearInterval(keepAliveIntervalId);
//         }
//       },
//       // Set the interval to 20 seconds to prevent the service worker from becoming inactive.
//       20 * 1000 
//     );
//   }

// function disconnect() {
//   if (webSocket == null) {
//     return;
//   }
//   webSocket.close();
// }

// chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
//     if (request.action === 'sendChatMessage') {
//         if (webSocket != null) {
//             webSocket.send(request.message);
//         }
//         return true;
//     }
//     return false;
// });

// chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
//     disconnect(); // disconnect for old tab
//     connect(); // conncet for new tab
// });

// chrome.runtime.onSuspend.addListener(() => {
//     disconnect(); // disconnect from websockets on service worker close    
// });