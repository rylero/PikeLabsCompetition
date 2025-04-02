// Display stored text when popup opens
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Popup opened');
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        console.log('Current tab:', tab.id);
        
        // First try to get stored text
        const storedText = await chrome.storage.local.get([`article_${tab.id}`]);
        console.log('Stored text exists:', !!storedText[`article_${tab.id}`]);
        
        if (storedText[`article_${tab.id}`]) {
            document.getElementById('textDisplay').textContent = storedText[`article_${tab.id}`];
            console.log('Displayed stored text');
        } else {
            // If no stored text, try to collect it immediately
            console.log('No stored text, attempting to collect');
            const result = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                function: () => {
                    const article = document.querySelector('article');
                    if (article) {
                        return Array.from(article.querySelectorAll('p')).map(p => p.innerText).join('\n\n');
                    }
                    return null;
                }
            });

            if (result && result.length > 0 && result[0].result) {
                document.getElementById('textDisplay').textContent = result[0].result;
                await chrome.storage.local.set({ [`article_${tab.id}`]: result[0].result });
                console.log('Collected and displayed new text');
            } else {
                document.getElementById('textDisplay').textContent = 'No article text found on this page.';
                console.log('No article text found');
            }
        }
    } catch (err) {
        console.error('Error in popup:', err);
        document.getElementById('textDisplay').textContent = 'Error: Could not load text.';
    }
});

// Keep the existing button click handler for manual refresh
document.getElementById('collectText').addEventListener('click', async () => {
    console.log('Manual refresh button clicked');
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    try {
        const result = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: () => {
                const article = document.querySelector('article');
                if (article) {
                    return Array.from(article.querySelectorAll('p')).map(p => p.innerText).join('\n\n');
                }
                return null;
            }
        });

        if (result && result.length > 0 && result[0].result) {
            document.getElementById('textDisplay').textContent = result[0].result;
            await chrome.storage.local.set({ [`article_${tab.id}`]: result[0].result });
            console.log('Manually refreshed text');
        } else {
            document.getElementById('textDisplay').textContent = 'No article text found on this page.';
            console.log('No article text found on manual refresh');
        }
    } catch (err) {
        console.error('Failed to execute script:', err);
        document.getElementById('textDisplay').textContent = 'Error: Could not collect text from this page.';
    }
});
