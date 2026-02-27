/**
 * FinanceAI - Dashboard Module
 * Handles dashboard charts and data visualization
 */

// Protect route
if (!isAuthenticated()) {
    window.location.href = '/login/';
}

// Chart.js default configuration
Chart.defaults.color = '#9ca3af';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.font.family = 'Inter, sans-serif';

// Base portfolio value used for random changes
const BASE_PORTFOLIO_VALUE = 124532.80;
let currentPortfolioValue = BASE_PORTFOLIO_VALUE;
const PORTFOLIO_UPDATE_INTERVAL_MS = 1000;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Start portfolio value updater first so it runs even if charts fail
    var valueEl = document.getElementById('portfolio-value');
    var changeEl = document.getElementById('portfolio-change');
    if (valueEl && changeEl) {
        updatePortfolioValueAndChange();
        setInterval(updatePortfolioValueAndChange, PORTFOLIO_UPDATE_INTERVAL_MS);
    }

    try {
        initPortfolioChart();
        initAllocationChart();
        initAccuracyChart();
        initSentimentChart();
    } catch (e) {
        console.warn('Dashboard charts init error', e);
    }
    initDashboardMarkets();
});

// Portfolio Growth Chart
let portfolioChartInstance = null;

function generatePortfolioData(days) {
    const labels = Array.from({length: days}, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (days - 1 - i));
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    // Generate realistic portfolio growth data with trend
    let value = 100000;
    const data = labels.map((_, i) => {
        const trendComponent = (i / days) * 5000; // Upward trend over time
        const volatility = (Math.random() - 0.4) * 2000;
        const change = trendComponent * (1 + volatility / 5000);
        value += change;
        return Math.max(value, 95000); // Ensure it doesn't drop too much
    });

    return { labels, data };
}

function updatePortfolioChart(timeRange) {
    const daysMap = {
        '1M': 30,
        '3M': 90,
        '1Y': 365
    };
    
    const days = daysMap[timeRange] || 30;
    const { labels, data } = generatePortfolioData(days);
    
    if (!portfolioChartInstance) {
        initPortfolioChart();
        return;
    }
    
    portfolioChartInstance.data.labels = labels;
    portfolioChartInstance.data.datasets[0].data = data;
    portfolioChartInstance.update();
}

function initPortfolioChart() {
    const ctx = document.getElementById('portfolioChart');
    if (!ctx) return;

    const { labels, data } = generatePortfolioData(30);

    portfolioChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value',
                data: data,
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#00d4ff',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
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
                            return '$' + context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2 });
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 6
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000) + 'k';
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Asset Allocation Pie Chart
function initAllocationChart() {
    const ctx = document.getElementById('allocationChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer', 'Other'],
            datasets: [{
                data: [35, 20, 18, 12, 10, 5],
                backgroundColor: [
                    '#00d4ff',
                    '#3b82f6',
                    '#8b5cf6',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
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
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            }
        }
    });
}

// Prediction Accuracy Bar Chart
function initAccuracyChart() {
    const ctx = document.getElementById('accuracyChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
            datasets: [{
                label: 'Your Accuracy',
                data: [65, 68, 72, 70, 75, 72],
                backgroundColor: '#00d4ff',
                borderRadius: 6,
                barPercentage: 0.6
            }, {
                label: 'AI Accuracy',
                data: [78, 80, 82, 79, 85, 83],
                backgroundColor: '#8b5cf6',
                borderRadius: 6,
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
                        padding: 20
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
                    grid: {
                        display: false
                    }
                },
                y: {
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

// Market Sentiment Chart
function initSentimentChart() {
    const ctx = document.getElementById('sentimentChart');
    if (!ctx) return;

    const labels = Array.from({length: 14}, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (13 - i));
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Bullish',
                data: [55, 58, 52, 60, 65, 62, 68, 70, 65, 72, 75, 70, 68, 72],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4
            }, {
                label: 'Bearish',
                data: [30, 28, 35, 25, 22, 24, 20, 18, 22, 16, 15, 18, 20, 18],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4
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
                        padding: 20
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
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 7
                    }
                },
                y: {
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
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Portfolio value – update every second; value and percentage turn green when up, red when down
function updatePortfolioValueAndChange() {
    var valueEl = document.getElementById('portfolio-value');
    var changeEl = document.getElementById('portfolio-change');
    var arrowEl = document.getElementById('portfolio-change-arrow');
    var textEl = document.getElementById('portfolio-change-text');
    if (!valueEl || !changeEl) return;

    var prev = currentPortfolioValue;
    var pctMove = (Math.random() - 0.5) * 0.6;
    currentPortfolioValue = prev * (1 + pctMove / 100);
    currentPortfolioValue = Math.max(80000, Math.min(180000, currentPortfolioValue));

    var changeDollar = currentPortfolioValue - prev;
    var pctChange = prev !== 0 ? (changeDollar / prev) * 100 : 0;
    var isUp = pctChange >= 0;

    valueEl.textContent = '$' + currentPortfolioValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    valueEl.classList.remove('positive', 'negative', 'portfolio-value-positive', 'portfolio-value-negative');
    valueEl.classList.add(isUp ? 'positive' : 'negative');
    valueEl.style.color = isUp ? '#22c55e' : '#ef4444';

    if (arrowEl) arrowEl.textContent = isUp ? '↑' : '↓';
    if (textEl) textEl.textContent = (isUp ? '+' : '') + pctChange.toFixed(2) + '% ($' + Math.abs(changeDollar).toLocaleString('en-US', { maximumFractionDigits: 0 }) + ')';
    changeEl.classList.remove('positive', 'negative');
    changeEl.classList.add(isUp ? 'positive' : 'negative');
    changeEl.style.color = isUp ? '#22c55e' : '#ef4444';
}

// Load dashboard data – legacy; portfolio now updated by updatePortfolioValueAndChange
async function loadDashboardData() {
    updatePortfolioValueAndChange();
}

// Update stat value with animation
function updateStatValue(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

// Dashboard Markets card – live update every 2 seconds
const DASHBOARD_MARKETS_INTERVAL_MS = 2000;
const DASHBOARD_MARKETS_DECIMALS = { nifty: 2, sensex: 2, gold: 2, silver: 2, usdinr: 3 };
const DASHBOARD_MARKETS_MIN = { nifty: 22000, sensex: 70000, gold: 4500, silver: 70, usdinr: 80 };
const DASHBOARD_MARKETS_MAX = { nifty: 27000, sensex: 90000, gold: 6500, silver: 110, usdinr: 100 };

function initDashboardMarkets() {
    const items = document.querySelectorAll('.dashboard-markets-item[data-market]');
    if (!items.length) return;

    const current = {};
    items.forEach(function(el) {
        const key = el.getAttribute('data-market');
        const valEl = el.querySelector('.dashboard-markets-value');
        if (!key || !valEl) return;
        const raw = valEl.textContent.replace(/,/g, '');
        current[key] = parseFloat(raw) || 0;
    });

    function formatValue(key, num) {
        const d = DASHBOARD_MARKETS_DECIMALS[key];
        if (d === 3) return num.toFixed(3);
        let s = num.toFixed(d);
        if (num >= 1000) {
            const parts = s.split('.');
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            s = parts.join('.');
        }
        return s;
    }

    function updateRow(el, key, newVal, pct) {
        const valEl = el.querySelector('.dashboard-markets-value');
        const chEl = el.querySelector('.dashboard-markets-change');
        if (!valEl || !chEl) return;
        valEl.textContent = formatValue(key, newVal);
        const sign = pct >= 0 ? '+' : '';
        chEl.textContent = sign + pct.toFixed(2) + '%';
        chEl.classList.remove('positive', 'negative');
        chEl.classList.add(pct >= 0 ? 'positive' : 'negative');
    }

    function tick() {
        items.forEach(function(el) {
            const key = el.getAttribute('data-market');
            if (!key || current[key] == null) return;
            const prev = current[key];
            const changePct = (Math.random() - 0.48) * 0.2;
            let newVal = prev * (1 + changePct / 100);
            const min = DASHBOARD_MARKETS_MIN[key], max = DASHBOARD_MARKETS_MAX[key];
            if (min != null && max != null) newVal = Math.max(min, Math.min(max, newVal));
            const pct = ((newVal - prev) / prev) * 100;
            current[key] = newVal;
            updateRow(el, key, newVal, pct);
        });
    }

    setInterval(tick, DASHBOARD_MARKETS_INTERVAL_MS);
}

// Refresh dashboard data
function refreshDashboard() {
    loadDashboardData();
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initPortfolioChart,
        initAllocationChart,
        initAccuracyChart,
        initSentimentChart,
        loadDashboardData
    };
}
