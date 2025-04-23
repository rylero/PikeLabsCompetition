// Display stored text when popup opens
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        // First try to get stored text
        const storedText = await chrome.storage.local.get([`article_${tab.id}`]);
        
        if (storedText[`article_${tab.id}`]) {
            document.getElementById('textDisplay').textContent = storedText[`article_${tab.id}`];
        } else {
            // If no stored text, request it from background script
            const response = await chrome.runtime.sendMessage({ 
                action: 'getArticleText', 
                tabId: tab.id 
            });
            
            if (response && response.text) {
                document.getElementById('textDisplay').textContent = response.text;
            } else {
                document.getElementById('textDisplay').textContent = 'No article text found on this page.';
            }
        }
    } catch (err) {
        document.getElementById('textDisplay').textContent = 'Error: Could not load text.';
    }
});

// Manual refresh button handler
document.getElementById('collectText').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    try {
        const response = await chrome.runtime.sendMessage({ 
            action: 'getArticleText', 
            tabId: tab.id 
        });
        
        if (response && response.text) {
            document.getElementById('textDisplay').textContent = response.text;
        } else {
            document.getElementById('textDisplay').textContent = 'No article text found on this page.';
        }
    } catch (err) {
        document.getElementById('textDisplay').textContent = 'Error: Could not collect text from this page.';
    }
});
