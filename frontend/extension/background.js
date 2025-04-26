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

// Listen for tab updates
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
        await collectArticleText(tabId);
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

// chrome.runtime.onInstalled.addListener(async () => {
// 	chrome.contextMenus.create({
// 		id: "analyze",
// 		title: "Analyze Article",
// 		type: 'normal'
// 	});
// });

// chrome.contextMenus.onClicked.addListener(async (item, tab) => {
//     text = collectArticleText(tab.id);
        
//     if (!text) {
//         returen;
//     }

//     let url = tab.url;
//     let tabId = tab.id;

//     const formData = new FormData();
//     formData.append("url", url);
//     formData.append("text", text);

//     const jsonResult = await fetch("http://0.0.0.0:8000/generate_report", {
//         method: "POST",
//         body: formData,
//     }).catch((err) => {
//         return null;
//     });

//     const analysis = await jsonResult.json();
//     console.log(analysis);

//     if (analysis == undefined || analysis == null) {
//         return;
//     }

//     chrome.storage.local.set({ [`analysis_${tabId}`]: analysis });
// });