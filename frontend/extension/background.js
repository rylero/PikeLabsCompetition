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
        console.log(result);

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
            console.log("News site openened");
        }

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
	});
});

chrome.contextMenus.onClicked.addListener(async (item, tab) => {
    let url = tab.url;
    let tabId = tab.id;

    let jsonResult = undefined;

    if (url.startsWith("https://www.youtube.com/watch")) {
        const formData = new FormData();
        formData.append("url", url);

        jsonResult = await fetch("http://0.0.0.0:8000/generate_report_from_youtube", {
            method: "POST",
            body: formData,
        }).catch((err) => {
            return null;
        });
    } else {
        let text = collectArticleText(tab.id);
        
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