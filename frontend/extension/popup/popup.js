const extpay = ExtPay('poliscan')
setPayBannerVisibility(false);

let user = {};
extpay.onPaid.addListener(currentUser => {
    user = currentUser;
    console.log(user);

    if (canUse(user)) {
        showLoadingScreen();
        if (user.paid) {
            setPayBannerVisibility(false);
        } else {
            setPayBannerVisibility(true);
        }
    } else {
        setPayBannerVisibility(true);
    }
})

// Carousel state
const carousels = {
    agreeing: { current: 0, items: 0 }, // Initialize items later
    disagreeing: { current: 0, items: 0 }
};

function setPayBannerVisibility(visible) {
    document.querySelector('.paywall').style.display = visible ? 'flex' : 'none';
    document.querySelector('.report').style['margin-top'] = visible ? '65px' : 0;
}

function showLoadingScreen() {
    const loader = document.querySelector('.loader');
    const report = document.querySelector('.report');

    loader.style.display = 'flex';
    report.style.display = 'none';
}


function setupReportPage() {
    // Attach event listeners to carousel arrows
    document.getElementById("agree-left").addEventListener('click', () => {
        moveCarousel("agreeing", -1);
    });
    document.getElementById("agree-right").addEventListener('click', () => {
        moveCarousel("agreeing", 1);
    });
    document.getElementById("disagree-left").addEventListener('click', () => {
        moveCarousel("disagreeing", -1);
    });
    document.getElementById("disagree-right").addEventListener('click', () => {
        moveCarousel("disagreeing", 1);
    });

}

function showReport(data) {
    const loader = document.querySelector('.loader');
    const report = document.querySelector('.report');

    loader.style.display = 'none';
    report.style.display = 'block';

    // Initialize gauges
    drawGauge(document.getElementById('biasGauge'), data.bias, 6, ['#1e88e5', '#4caf50', '#d81b60'], true);
    drawGauge(document.getElementById('credibilityGauge'), data.factuality, 6, ['#d81b60', '#4caf50']);

    document.getElementById("bias-gauge-container").display = data["show-bias"] ? 'block' : 'none';
    document.getElementById("credibility-content").textContent = data.factuality_description;
    document.getElementById("bias-content").textContent = data.bias_description;

    const agreeContainer = document.getElementById("agreeingInner");
    data.agreement_links.forEach((d) => {
        const a = document.createElement("a")
        a.href = d.link;
        a.innerText = d.title;
        a.className = "carousel-item";
        a.target = "_blank";

        agreeContainer.appendChild(a);
    })

    const disagreeContainer = document.getElementById("disagreeingInner");
    data.opposing_links.forEach((d) => {
        const a = document.createElement("a")
        a.href = d.link;
        a.innerText = d.title;
        a.className = "carousel-item";
        a.target = "_blank";

        disagreeContainer.appendChild(a);
    })

    updateCarouselWidths();
}

// Gauge drawing function
function drawGauge(canvas, score, maxScore, colors, isBiasGauge = false) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width = 180;
    const height = canvas.height = 90;
    const centerX = width / 2;
    const centerY = height;
    const radius = 70;
    const startAngle = Math.PI * 0.75;
    const endAngle = Math.PI * 2.25;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, startAngle, endAngle);
    ctx.lineWidth = 15;
    ctx.strokeStyle = '#444';
    ctx.stroke();

    // Gradient arc
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    colors.forEach((color, i) => {
        gradient.addColorStop(i / (colors.length - 1), color);
    });

    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, startAngle, endAngle);
    ctx.strokeStyle = gradient;
    ctx.stroke();

    // Needle (tapered and slightly opaque)
    const normalizedScore = isBiasGauge ? (score + 3) : score;
    let angle = startAngle + (normalizedScore / maxScore) * (endAngle - startAngle);
    angle = Math.min(Math.max(angle, Math.PI + 0.1), Math.PI * 2 - 0.1);
    const needleStart = 10;
    const needleEnd = radius + 5;
    const baseWidth = 6;
    const tipWidth = 2;

    ctx.globalAlpha = 0.8;
    ctx.beginPath();
    ctx.moveTo(
        centerX + needleStart * Math.cos(angle) - (baseWidth / 2) * Math.sin(angle),
        centerY + needleStart * Math.sin(angle) + (baseWidth / 2) * Math.cos(angle)
    );
    ctx.lineTo(
        centerX + needleStart * Math.cos(angle) + (baseWidth / 2) * Math.sin(angle),
        centerY + needleStart * Math.sin(angle) - (baseWidth / 2) * Math.cos(angle)
    );
    ctx.lineTo(
        centerX + needleEnd * Math.cos(angle) + (tipWidth / 2) * Math.sin(angle),
        centerY + needleEnd * Math.sin(angle) - (tipWidth / 2) * Math.cos(angle)
    );
    ctx.lineTo(
        centerX + needleEnd * Math.cos(angle) - (tipWidth / 2) * Math.sin(angle),
        centerY + needleEnd * Math.sin(angle) + (tipWidth / 2) * Math.cos(angle)
    );
    ctx.closePath();
    ctx.fillStyle = '#cccccc';
    ctx.fill();
    ctx.globalAlpha = 1.0;

    // Update bias gauge text
    if (isBiasGauge) {
        const biasText = score <= -2 ? 'Left' :
            score <= -1 ? 'Slight Left' :
                score <= 0 ? 'Moderate' :
                    score <= 1 ? 'Slight Right' : 'Right';
        document.getElementById('biasScore').textContent = biasText;
    } else {
        document.getElementById('credibilityScore').textContent = score + "/5";
    }
}

function updateCarouselWidths() {
    const agreeingInner = document.getElementById('agreeingInner');
    const disagreeingInner = document.getElementById('disagreeingInner');
    if (!agreeingInner || !disagreeingInner) {
        console.error('Carousel inner elements not found');
        return;
    }

    carousels.agreeing.items = agreeingInner.querySelectorAll('.carousel-item').length;
    carousels.disagreeing.items = disagreeingInner.querySelectorAll('.carousel-item').length;
}

function moveCarousel(type, direction) {
    if (!carousels[type]) {
        console.error(`Invalid carousel type: ${type}. Expected 'agreeing' or 'disagreeing'.`);
        return;
    }
    const carousel = carousels[type];
    carousel.current = (carousel.current + direction + carousel.items) % carousel.items;
    const inner = document.getElementById(`${type}Inner`);
    if (!inner) {
        console.error(`Carousel inner element not found for type: ${type}`);
        return;
    }
    const items = inner.querySelectorAll('.carousel-item');
    items.forEach(item => {
        item.style.transform = `translateX(-${(carousel.current * 340)}px)`;
    });
}

async function startAnalyzing(tabId, url, content) {
    const formData = new FormData();
    formData.append("url", url);
    formData.append("text", content);

    const jsonResult = await fetch("http://192.168.1.20:34052/generate_report", {
        method: "POST",
        body: formData,
    }).catch((err) => {
        return null;
    });

    const analysis = await jsonResult.json();

    if (analysis == undefined || analysis == null) {
        document.getElementById('loading-text').textContent = "Analysis Failed";
    }
    chrome.storage.local.set({ [`analysis_${tabId}`]: analysis });

    setupReportPage();

    // Collapsible sections
    const collapsibles = document.getElementsByClassName('collapsible');
    for (let i = 0; i < collapsibles.length; i++) {
        collapsibles[i].addEventListener('click', function () {
            this.classList.toggle('active');
            const content = this.nextElementSibling;
            content.style.display = content.style.display === 'block' ? 'none' : 'block';
        });
    }

    showReport(analysis);
}

function canUse(user) {
    const now = new Date();
    const sevenDays = 1000*60*60*24*7;
    return user.paid || (user.trialStartedAt && (now - user.trialStartedAt) < sevenDays);
}

document.addEventListener('DOMContentLoaded', async () => {
    extpay.getUser().then(async currentUser => {
        user = currentUser;
        console.log(user);
        
        if (user.email) {
            document.getElementById('login-button').style.display = 'none';
        }

        if (user.trialStartedAt) {
            document.getElementById('freetrial-button').style.display = 'none';
        }

        if (!canUse(user)) {
            document.getElementById('loading-text').textContent = "Waiting for payment...";
            setPayBannerVisibility(true);
            return;
        }
        
        if (user.paid) {
            setPayBannerVisibility(false);
        } else {
            document.getElementById("paywalltitle").textContent = "Your account is currently on a free trial"
            setPayBannerVisibility(true);
        }

        showLoadingScreen();
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

            // first check ai analyzsis
            const storedAnalysis = await chrome.storage.local.get([`analysis_${tab.id}`]);
            if (storedAnalysis[`analysis_${tab.id}`]) {
                setupReportPage();

                // Collapsible sections
                const collapsibles = document.getElementsByClassName('collapsible');
                for (let i = 0; i < collapsibles.length; i++) {
                    collapsibles[i].addEventListener('click', function () {
                        this.classList.toggle('active');
                        const content = this.nextElementSibling;
                        content.style.display = content.style.display === 'block' ? 'none' : 'block';
                    });
                }

                showReport(storedAnalysis);
            }

            // Second try to get stored text
            const storedText = await chrome.storage.local.get([`article_${tab.id}`]);

            if (storedText[`article_${tab.id}`]) {
                document.getElementById('loading-text').textContent = "Article Text Loaded";
                startAnalyzing(tab.url, storedText[`article_${tab.id}`]);
            } else {
                // If no stored text, request it from background script
                const response = await chrome.runtime.sendMessage({
                    action: 'getArticleText',
                    tabId: tab.id
                });

                if (response && response.text) {
                    document.getElementById('loading-text').textContent = "Article Text Loaded";
                    startAnalyzing(tab.id, tab.url, response.text);
                } else {
                    document.getElementById('loading-text').textContent = 'No article text found on this page.';
                }
            }
        } catch (err) {
            console.error(err);
            document.getElementById('loading-text').textContent = 'Error: Could not load text.';
        }
    });
});

document.getElementById("payment-button").addEventListener("click", () => {
    extpay.openPaymentPage();
});

document.getElementById("freetrial-button").addEventListener("click", () => {
    extpay.openTrialPage();
});

document.getElementById("login-button").addEventListener("click", () => {
    extpay.openLoginPage();
});