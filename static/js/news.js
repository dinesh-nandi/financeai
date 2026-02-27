/**
 * FinanceAI - News Intelligence Module
 * Handles news sentiment analysis and visualization
 */

// Protect route
if (!isAuthenticated()) {
    window.location.href = '/login/';
}

// Initialize news page
document.addEventListener('DOMContentLoaded', function() {
    initSentimentGauge();
    initSentimentTrendChart();
    initCorrelationChart();
    loadNewsData();
    
    // Setup correlation help button - Toggle instructions panel
    const helpBtn = document.getElementById('correlationHelpBtn');
    const instructionsPanel = document.getElementById('correlationInstructions');
    
    if (helpBtn && instructionsPanel) {
        // Click to toggle
        helpBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const isHidden = instructionsPanel.style.display === 'none';
            instructionsPanel.style.display = isHidden ? 'block' : 'none';
            helpBtn.setAttribute('aria-expanded', isHidden);
            
            // Update button visual feedback
            if (isHidden) {
                helpBtn.style.background = 'rgba(0, 212, 255, 0.15)';
                helpBtn.style.borderColor = 'var(--accent-cyan)';
            } else {
                helpBtn.style.background = 'var(--bg-glass)';
                helpBtn.style.borderColor = 'var(--border-color)';
            }
        });
        
        // Close when clicking outside
        document.addEventListener('click', function(e) {
            if (instructionsPanel.style.display !== 'none' && 
                !instructionsPanel.contains(e.target) && 
                e.target !== helpBtn) {
                instructionsPanel.style.display = 'none';
                helpBtn.style.background = 'var(--bg-glass)';
                helpBtn.style.borderColor = 'var(--border-color)';
            }
        });
    }
});

// Sentiment Gauge Chart
function initSentimentGauge() {
    const ctx = document.getElementById('sentimentGauge');
    if (!ctx) return;

    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [68, 18, 14],
                backgroundColor: [
                    '#10b981',
                    '#ef4444',
                    '#f59e0b'
                ],
                borderWidth: 0,
                cutout: '70%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#9ca3af',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'gaugeText',
            beforeDraw: function(chart) {
                const width = chart.width,
                      height = chart.height,
                      ctx = chart.ctx;

                ctx.restore();
                const fontSize = (height / 114).toFixed(2);
                ctx.font = `bold ${fontSize}em Inter, sans-serif`;
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#10b981';

                const text = 'Bullish',
                      textX = Math.round((width - ctx.measureText(text).width) / 2),
                      textY = height / 2;

                ctx.fillText(text, textX, textY);
                
                ctx.font = `${(height / 200).toFixed(2)}em Inter, sans-serif`;
                ctx.fillStyle = '#9ca3af';
                const subtext = 'Overall Sentiment',
                      subtextX = Math.round((width - ctx.measureText(subtext).width) / 2),
                      subtextY = height / 2 + 25;
                ctx.fillText(subtext, subtextX, subtextY);
                
                ctx.save();
            }
        }]
    });
}

// Sentiment Trend Chart (7 days)
function initSentimentTrendChart() {
    const ctx = document.getElementById('sentimentTrendChart');
    if (!ctx) return;

    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Positive',
                data: [55, 62, 58, 70, 75, 68, 72],
                backgroundColor: '#10b981',
                borderRadius: 4,
                barPercentage: 0.6
            }, {
                label: 'Negative',
                data: [25, 20, 28, 18, 15, 20, 18],
                backgroundColor: '#ef4444',
                borderRadius: 4,
                barPercentage: 0.6
            }, {
                label: 'Neutral',
                data: [20, 18, 14, 12, 10, 12, 10],
                backgroundColor: '#f59e0b',
                borderRadius: 4,
                barPercentage: 0.6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#9ca3af',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: {
                        display: false
                    }
                },
                y: {
                    stacked: true,
                    min: 0,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Correlation / Advanced Technical Chart (Price vs Sentiment with EMA7, MACD, ROC)
function initCorrelationChart() {
    const ctx = document.getElementById('correlationChart');
    if (!ctx) return;

    // --- Helper functions for technical indicators ---
    function ema(values, period) {
        const k = 2 / (period + 1);
        const result = [];
        let prev;
        values.forEach((v, i) => {
            if (i === 0) {
                prev = v;
                result.push(v);
            } else {
                const curr = v * k + prev * (1 - k);
                result.push(curr);
                prev = curr;
            }
        });
        return result;
    }

    function macd(values, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        const fast = ema(values, fastPeriod);
        const slow = ema(values, slowPeriod);
        const macdLine = values.map((_, i) => fast[i] - slow[i]);
        const signalLine = ema(macdLine, signalPeriod);
        const histogram = macdLine.map((v, i) => v - signalLine[i]);
        return { macdLine, signalLine, histogram };
    }

    function roc(values, period = 7) {
        return values.map((v, i) => {
            if (i < period) return 0;
            const prev = values[i - period];
            return prev ? ((v - prev) / prev) * 100 : 0;
        });
    }

    // --- Generate synthetic price + sentiment data for demonstration ---
    const points = 60;
    const labels = Array.from({ length: points }, (_, i) => `Day ${i + 1}`);

    let price = [];
    let last = 100;
    for (let i = 0; i < points; i++) {
        // Random walk with gentle drift
        const change = (Math.random() - 0.5) * 2; // -1% to +1%
        last = last * (1 + change / 100);
        price.push(Number(last.toFixed(2)));
    }

    const ema7 = ema(price, 7).map(v => Number(v.toFixed(2)));
    const macdData = macd(price);
    const macdLine = macdData.macdLine.map(v => Number(v.toFixed(3)));
    const signalLine = macdData.signalLine.map(v => Number(v.toFixed(3)));
    const histogram = macdData.histogram.map(v => Number(v.toFixed(3)));
    const roc7 = roc(price, 7).map(v => Number(v.toFixed(2)));

    // News sentiment scores between -1 and +1 (scaled to %)
    const sentiment = Array.from({ length: points }, () =>
        Number(((Math.random() - 0.2) * 80).toFixed(1)) // tilt slightly positive
    );

    new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {   // 0 - Price (hidden by default)
                    label: 'Price',
                    data: price,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.15)',
                    tension: 0.25,
                    yAxisID: 'yPrice',
                    pointRadius: 0,
                    borderWidth: 2,
                    hidden: true
                },
                {   // 1 - EMA7 (hidden by default)
                    label: 'EMA 7',
                    data: ema7,
                    borderColor: '#f59e0b',
                    borderDash: [4, 4],
                    tension: 0.25,
                    yAxisID: 'yPrice',
                    pointRadius: 0,
                    borderWidth: 2,
                    hidden: true
                },
                {   // 2 - MACD line (hidden by default)
                    label: 'MACD',
                    data: macdLine,
                    borderColor: '#10b981',
                    tension: 0.2,
                    yAxisID: 'yInd',
                    pointRadius: 0,
                    borderWidth: 1.5,
                    hidden: true
                },
                {   // 3 - Signal line (hidden by default)
                    label: 'Signal',
                    data: signalLine,
                    borderColor: '#ef4444',
                    tension: 0.2,
                    yAxisID: 'yInd',
                    pointRadius: 0,
                    borderWidth: 1.2,
                    hidden: true
                },
                {   // 4 - MACD histogram (hidden by default)
                    type: 'bar',
                    label: 'MACD Histogram',
                    data: histogram,
                    yAxisID: 'yInd',
                    backgroundColor: histogram.map(v =>
                        v >= 0 ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
                    ),
                    borderWidth: 0,
                    barPercentage: 0.6,
                    categoryPercentage: 0.9,
                    hidden: true
                },
                {   // 5 - ROC (hidden by default)
                    label: 'ROC 7 (%)',
                    data: roc7,
                    borderColor: '#8b5cf6',
                    borderDash: [2, 2],
                    tension: 0.2,
                    yAxisID: 'yInd',
                    pointRadius: 0,
                    borderWidth: 1.2,
                    hidden: true
                },
                {   // 6 - Sentiment (visible by default)
                    label: 'News Sentiment (%)',
                    data: sentiment,
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.08)',
                    tension: 0.25,
                    yAxisID: 'ySent',
                    pointRadius: 0,
                    borderWidth: 1.5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        color: '#e5e7eb'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#9ca3af',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || '';
                            const v = context.parsed.y;
                            if (label === 'Price' || label === 'EMA 7') {
                                return `${label}: ${v.toFixed(2)}`;
                            }
                            if (label === 'ROC 7 (%)' || label === 'News Sentiment (%)') {
                                return `${label}: ${v.toFixed(2)}%`;
                            }
                            return `${label}: ${v.toFixed(3)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.04)'
                    },
                    ticks: {
                        color: '#6b7280',
                        maxTicksLimit: 8
                    }
                },
                yPrice: {
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Price',
                        color: '#9ca3af'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.06)'
                    },
                    ticks: {
                        color: '#6b7280',
                        callback: function (value) {
                            return value.toFixed(0);
                        }
                    }
                },
                yInd: {
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Indicators (MACD, ROC)',
                        color: '#9ca3af'
                    },
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6b7280'
                    }
                },
                ySent: {
                    position: 'right',
                    display: false,
                    title: {
                        display: true,
                        text: 'Sentiment (%)',
                        color: '#9ca3af'
                    }
                }
            }
        }
    });

    // Hook up indicator toggles so user can choose what to show
    const toggleConfig = [
        { id: 'indicator-toggle-sentiment', datasets: [6] },
        { id: 'indicator-toggle-price', datasets: [0] },
        { id: 'indicator-toggle-ema7', datasets: [1] },
        { id: 'indicator-toggle-macd', datasets: [2, 3, 4] },
        { id: 'indicator-toggle-roc', datasets: [5] },
    ];

    toggleConfig.forEach(cfg => {
        const el = document.getElementById(cfg.id);
        if (!el) return;
        // Initialize checkbox state based on dataset.hidden
        const firstMeta = chart.getDatasetMeta(cfg.datasets[0]);
        el.checked = !firstMeta.hidden;
        el.addEventListener('change', function () {
            cfg.datasets.forEach(index => {
                const meta = chart.getDatasetMeta(index);
                meta.hidden = !el.checked;
            });
            chart.update();
        });
    });
}

// Render live news cards into grid
function renderNewsCards(articles, bannerMessage) {
    const container = document.getElementById('news-list');
    if (!container) return;

    container.innerHTML = '';

    if (bannerMessage) {
        const banner = document.createElement('div');
        banner.className = 'glass-card';
        banner.style.cssText = 'padding: 12px 16px; margin-bottom: 16px; background: rgba(0, 212, 255, 0.08); border-left: 4px solid var(--accent-cyan);';
        banner.innerHTML = '<p style="margin: 0; font-size: 13px; color: var(--text-secondary);">' + (bannerMessage.replace(/</g, '&lt;').replace(/>/g, '&gt;')) + '</p>';
        container.appendChild(banner);
    }

    if (!articles.length) {
        const empty = document.createElement('div');
        empty.className = 'glass-card';
        empty.style.padding = '24px';
        empty.innerHTML = '<p style="color: var(--text-secondary); font-size: 14px;">No live news articles available right now.</p>';
        container.appendChild(empty);
        return;
    }

// Format published date; if invalid or missing, use today's date with random time in IST
function formatNewsDate(publishedAt) {
    if (publishedAt) {
        try {
            var d = new Date(publishedAt);
            if (!isNaN(d.getTime())) {
                return d.toLocaleString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                }) + ' IST';
            }
        } catch (e) {}
    }
    var now = new Date();
    var hour = Math.floor(Math.random() * 18) + 6;
    var minute = Math.floor(Math.random() * 60);
    var d = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hour, minute);
    return d.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }) + ' IST';
}

    articles.forEach(article => {
        const card = document.createElement('div');
        card.className = 'glass-card';
        card.style.padding = '24px';

        const published = formatNewsDate(article.published_at);

        const impact = (article.impact || '').toLowerCase();
        const impactLabel = impact === 'high' ? 'High' : (impact === 'med' ? 'Med' : (impact === 'low' ? 'Low' : ''));
        const ledClass = impact === 'high' ? 'led-dot-led-hard' : (impact === 'med' ? 'led-dot-led-med' : (impact === 'low' ? 'led-dot-led-easy' : ''));

        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <span class="sentiment sentiment-neutral">Live</span>
                ${impactLabel && ledClass ? `<span class="led-indicator"><span class="led-dot ${ledClass}"></span>${impactLabel}</span>` : ''}
                <span style="font-size: 12px; color: var(--text-secondary);">
                    ${published}${article.source ? ' • ' + article.source : ''}
                </span>
            </div>
            <h4 style="margin-bottom: 12px; line-height: 1.4;">${article.title || 'Untitled'}</h4>
            <p style="color: var(--text-secondary); font-size: 14px; line-height: 1.6; margin-bottom: 16px;">
                ${article.summary || ''}
            </p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 12px; color: var(--text-muted);">
                    ${article.source || ''}
                </span>
                <a href="${article.url || '#'}" target="_blank" rel="noopener noreferrer" style="color: var(--accent-cyan); font-size: 14px;">
                    Read more →
                </a>
            </div>
        `;

        container.appendChild(card);
    });
}

// Load news data
async function loadNewsData() {
    const container = document.getElementById('news-list');
    try {
        const base = (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : '';
        const url = (base + '/api/news/live/').replace(/([^:]\/)\/+/g, '$1');
        const response = await fetch(url, { credentials: 'same-origin' });

        if (!response.ok) {
            const raw = await response.text();
            showNewsError(container, 'Failed to load live news from server.', raw);
            return;
        }

        const payload = await response.json();
        if (!payload || payload.status !== 'success' || !payload.data) {
            const msg = (payload && payload.message) || 'Invalid response from news API.';
            showNewsError(container, msg);
            return;
        }

        const articles = payload.data.articles || [];
        const source = payload.data.source;
        renderNewsCards(articles);
    } catch (error) {
        console.error('Error loading news data:', error);
        showNewsError(container, 'Unable to load live news right now. Please try again later.');
    }
}

function showNewsError(container, message, raw) {
    if (!container) return;
    container.innerHTML = `
        <div class="glass-card" style="padding: 24px;">
            <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 8px;">
                ${message}
            </p>
            ${raw ? `<pre style="white-space: pre-wrap; font-size: 11px; color: var(--text-muted); max-height: 200px; overflow-y: auto;">${raw}</pre>` : ''}
        </div>
    `;
}

// Filter news by category
function filterNews(category) {
    console.log('Filtering news by:', category);
    // In production, implement actual filtering
}

// Filter news by sentiment
function filterBySentiment(sentiment) {
    console.log('Filtering by sentiment:', sentiment);
    // In production, implement actual filtering
}

// Filter news by impact
function filterByImpact(impact) {
    console.log('Filtering by impact:', impact);
    // In production, implement actual filtering
}

// Search news
function searchNews(query) {
    console.log('Searching news:', query);
    // In production, implement actual search
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initSentimentGauge,
        initSentimentTrendChart,
        initCorrelationChart,
        loadNewsData
    };
}
