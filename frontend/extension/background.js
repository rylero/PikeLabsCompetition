// Function to collect article text
async function collectArticleText(tabId) {
    try {
        const result = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            function: () => {
                const article = document.querySelector('article');
                if (article) {
                    return Array.from(article.querySelectorAll('p')).map(p => p.innerText).join('\n\n');
                }
                return null;
            }
        });

        if (result && result.length > 0 && result[0].result) {
            await chrome.storage.local.set({ [`article_${tabId}`]: result[0].result });
            console.log('Storing text for tab:', tabId);
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
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getArticleText') {
        collectArticleText(request.tabId).then(text => {
            sendResponse({ text: text });
        });
        return true; // Required for async response
    }
    return false; // Return false if not handling the message
}); 