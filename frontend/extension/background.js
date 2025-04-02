chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    console.log('Tab updated:', tabId, changeInfo.status);
    if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
        try {
            console.log('Attempting to collect text from tab:', tabId);
            const result = await chrome.scripting.executeScript({
                target: { tabId: tabId },
                function: () => {
                    const article = document.querySelector('article');
                    console.log('Article found:', !!article);
                    if (article) {
                        const paragraphs = article.querySelectorAll('p');
                        console.log('Number of paragraphs found:', paragraphs.length);
                        return Array.from(paragraphs).map(p => p.innerText).join('\n\n');
                    }
                    return null;
                }
            });

            console.log('Script execution result:', result);
            if (result && result.length > 0 && result[0].result) {
                console.log('Storing text for tab:', tabId);
                await chrome.storage.local.set({ [`article_${tabId}`]: result[0].result });
                // Verify storage
                const stored = await chrome.storage.local.get([`article_${tabId}`]);
                console.log('Verified storage:', !!stored[`article_${tabId}`]);
            }
        } catch (err) {
            console.error('Failed to collect article text:', err);
        }
    }
}); 