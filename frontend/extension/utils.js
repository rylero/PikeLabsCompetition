export const analyzeArticle = async (url, text) => {
    try {
        const formData = new FormData();
        formData.append("url", url);
        if (text) formData.append("text", text);

        const endpoint = url.startsWith("https://www.youtube.com/watch") 
            ? "https://poltiscan-service-1092122045742.us-central1.run.app/generate_report_from_youtube"
            : "https://poltiscan-service-1092122045742.us-central1.run.app/generate_report";

        const response = await fetch(endpoint, {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const analysis = await response.json();
        if (!analysis) throw new Error("No analysis data received");

        return analysis;
    } catch (error) {
        console.error("Analysis failed:", error);
        return null;
    }
};

export const setupCollapsibles = () => {
    const collapsibles = document.getElementsByClassName('collapsible');
    for (let i = 0; i < collapsibles.length; i++) {
        collapsibles[i].addEventListener('click', function() {
            this.classList.toggle('active');
            const content = this.nextElementSibling;
            if (content) {
                content.style.display = content.style.display === 'block' ? 'none' : 'block';
            }
        });
    }
}; 