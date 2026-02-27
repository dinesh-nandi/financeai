/**
 * FinanceAI - Portfolio Module
 * Handles portfolio tracking, analysis, and visualization
 */

// Protect route
if (!isAuthenticated()) {
    window.location.href = '/login/';
}

// Portfolio data
let portfolio = [
    { symbol: 'AAPL', name: 'Apple Inc.', shares: 50, avgPrice: 150.00, currentPrice: 182.50 },
    { symbol: 'TSLA', name: 'Tesla Inc.', shares: 30, avgPrice: 200.00, currentPrice: 215.30 },
    { symbol: 'INFY', name: 'Infosys Ltd.', shares: 100, avgPrice: 18.50, currentPrice: 19.85 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', shares: 25, avgPrice: 280.00, currentPrice: 312.45 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', shares: 40, avgPrice: 130.00, currentPrice: 141.20 }
];

// Initialize portfolio page
document.addEventListener('DOMContentLoaded', function() {
    initAllocationChart();
    initPerformanceChart();
    initNewsEffectChart();
    bindNewsEffectRangeSelector();
    updatePortfolioTable();
    updatePortfolioSummary();
    
    // Continuously update summary every 2 seconds to simulate live changes
    setInterval(updatePortfolioSummary, 2000);
    
    // Setup add stock form
    const addStockForm = document.getElementById('add-stock-form');
    if (addStockForm) {
        addStockForm.addEventListener('submit', handleAddStock);
    }

    // Auto-fill purchase price with live share price when symbol is entered
    const symbolInput = document.getElementById('stock-symbol');
    if (symbolInput) {
        symbolInput.addEventListener('blur', async function () {
            const raw = symbolInput.value.trim();
            if (!raw) return;
            const symbol = raw.toUpperCase();
            await fetchAndSetLivePurchasePrice(symbol);
        });
    }
});

// Initialize allocation pie chart
function initAllocationChart() {
    const ctx = document.getElementById('allocationChart');
    if (!ctx) return;

    // Calculate allocation by stock
    const labels = portfolio.map(p => p.symbol);
    const data = portfolio.map(p => p.shares * p.currentPrice);
    const total = data.reduce((a, b) => a + b, 0);
    const percentages = data.map(v => ((v / total) * 100).toFixed(1));

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: percentages,
                backgroundColor: [
                    '#00d4ff',
                    '#3b82f6',
                    '#8b5cf6',
                    '#10b981',
                    '#f59e0b'
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
                        pointStyle: 'circle',
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
                        }
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
                            const value = data[context.dataIndex];
                            return context.label + ': $' + value.toLocaleString('en-US', { minimumFractionDigits: 2 }) + ' (' + context.parsed + '%)';
                        }
                    }
                }
            }
        }
    });
}

// Initialize performance line chart
function initPerformanceChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;

    const labels = Array.from({length: 30}, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (29 - i));
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    // Generate portfolio performance data
    let value = 100000;
    const data = labels.map(() => {
        const change = (Math.random() - 0.35) * 1500;
        value += change;
        return value;
    });

    new Chart(ctx, {
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

// Normal price vs after-news-effect comparison chart — daily + 5–6 time frames (1D, 5D, 1W, 1M, 3M, 6M)
let newsEffectChartInstance = null;
let cachedNewsImpacts = {};

function getNewsEffectRange() {
    const el = document.getElementById('news-effect-range');
    return (el && el.value) ? el.value : '1M';
}

function getPointsForRange(range) {
    switch (range) {
        case '1D': return 24;
        case '5D': return 5;
        case '1W': return 7;
        case '1M': return 30;
        case '3M': return 15;
        case '6M': return 20;
        default: return 30;
    }
}

function getLabelFormat(range) {
    if (range === '1D') return { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return { month: 'short', day: 'numeric' };
}

async function initNewsEffectChart() {
    const ctx = document.getElementById('newsEffectChart');
    if (!ctx) return;

    const range = getNewsEffectRange();
    const numPoints = getPointsForRange(range);
    const labelFormat = getLabelFormat(range);
    const currentValue = portfolio.reduce((sum, p) => sum + p.shares * p.currentPrice, 0);
    if (currentValue <= 0) return;

    if (Object.keys(cachedNewsImpacts).length === 0 && portfolio.length > 0) {
        for (let i = 0; i < portfolio.length; i++) {
            const sym = portfolio[i].symbol;
            cachedNewsImpacts[sym] = await getNewsImpactForSymbol(sym);
        }
    }

    const now = new Date();
    const labels = [];
    const normalValues = [];
    const newsEffectValues = [];
    const daysBack = range === '1D' ? 1/24 : range === '5D' ? 5 : range === '1W' ? 7 : range === '1M' ? 30 : range === '3M' ? 90 : 180;
    const step = daysBack / Math.max(1, numPoints - 1);
    let normalVal = currentValue * (1 - (daysBack / 365) * 0.05);
    const drift = (currentValue - normalVal) / Math.max(1, numPoints - 1);

    for (let i = 0; i < numPoints; i++) {
        const d = new Date(now);
        if (range === '1D') d.setHours(d.getHours() - (numPoints - 1 - i));
        else d.setDate(d.getDate() - (daysBack - i * step));
        labels.push(d.toLocaleDateString('en-US', labelFormat));
        normalVal += drift + (Math.random() - 0.5) * currentValue * 0.002;
        if (i === numPoints - 1) normalVal = currentValue;
        normalValues.push(Math.round(normalVal * 100) / 100);
        const portfolioImpact = portfolio.reduce((acc, p) => {
            const weight = (p.shares * p.currentPrice) / currentValue;
            return acc + (cachedNewsImpacts[p.symbol] != null ? cachedNewsImpacts[p.symbol] : 0) * weight;
        }, 0) / 100;
        const newsVal = normalVal * (1 + portfolioImpact * (0.3 + 0.7 * i / numPoints));
        newsEffectValues.push(Math.round(newsVal * 100) / 100);
    }
    normalValues[normalValues.length - 1] = currentValue;
    const lastImpact = portfolio.reduce((acc, p) => {
        const w = (p.shares * p.currentPrice) / currentValue;
        return acc + (cachedNewsImpacts[p.symbol] != null ? cachedNewsImpacts[p.symbol] : 0) * w;
    }, 0) / 100;
    newsEffectValues[newsEffectValues.length - 1] = Math.round(currentValue * (1 + lastImpact) * 100) / 100;

    if (newsEffectChartInstance) {
        newsEffectChartInstance.destroy();
        newsEffectChartInstance = null;
    }

    newsEffectChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Normal value',
                    data: normalValues,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.12)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: range === '1D' ? 2 : 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#00d4ff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 1
                },
                {
                    label: 'After news effect',
                    data: newsEffectValues,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: range === '1D' ? 2 : 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { padding: 16, usePointStyle: true, color: 'var(--text-primary)' } },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#e5e7eb',
                    borderColor: 'rgba(255,255,255,0.1)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const v = context.parsed.y;
                            return context.dataset.label + ': $' + (typeof v === 'number' ? v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : v);
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { maxTicksLimit: 10, color: 'var(--text-secondary)' } },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.06)' },
                    ticks: {
                        callback: function(v) { return '$' + (typeof v === 'number' ? (v >= 1000 ? (v/1000).toFixed(1) + 'k' : v.toFixed(0)) : v); },
                        color: 'var(--text-secondary)'
                    }
                }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

function bindNewsEffectRangeSelector() {
    const sel = document.getElementById('news-effect-range');
    if (!sel) return;
    sel.addEventListener('change', function() {
        cachedNewsImpacts = {};
        initNewsEffectChart();
    });
}

// Get news sentiment impact as % (positive = price up, negative = price down). Uses API when available.
async function getNewsImpactForSymbol(symbol) {
    try {
        const base = (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : '';
        const url = (base + '/api/prediction/stocks/' + encodeURIComponent(symbol) + '/sentiment/').replace(/([^:]\/)\/+/g, '$1');
        const res = await fetch(url, { credentials: 'same-origin' });
        if (!res.ok) return mockNewsImpact(symbol);
        const data = await res.json();
        const payload = data && data.data;
        if (!payload) return mockNewsImpact(symbol);
        var score = payload.sentiment_score != null ? parseFloat(payload.sentiment_score) : null;
        if (score == null && payload.distribution) {
            var d = payload.distribution;
            score = ((d.positive || 0) - (d.negative || 0)) / 100;
        }
        if (score == null) return mockNewsImpact(symbol);
        return Math.max(-5, Math.min(5, score * 4));
    } catch (e) {
        return mockNewsImpact(symbol);
    }
}

function mockNewsImpact(symbol) {
    const hash = (symbol + 'news').split('').reduce((a, c) => ((a << 5) - a) + c.charCodeAt(0), 0);
    return ((hash % 90) - 45) / 10;
}

// Update portfolio table
function updatePortfolioTable() {
    const tableBody = document.querySelector('#portfolio-table tbody');
    if (!tableBody) return;

    tableBody.innerHTML = portfolio.map(stock => {
        const marketValue = stock.shares * stock.currentPrice;
        const costBasis = stock.shares * stock.avgPrice;
        const gainLoss = marketValue - costBasis;
        const percentChange = ((stock.currentPrice - stock.avgPrice) / stock.avgPrice) * 100;
        const isPositive = gainLoss >= 0;

        return `
            <tr>
                <td style="font-weight: 600;">${stock.symbol}</td>
                <td>${stock.name}</td>
                <td>${stock.shares}</td>
                <td>$${stock.avgPrice.toFixed(2)}</td>
                <td>$${stock.currentPrice.toFixed(2)}</td>
                <td>$${marketValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                <td class="${isPositive ? 'text-green' : 'text-red'}">${isPositive ? '+' : ''}$${gainLoss.toFixed(2)}</td>
                <td class="${isPositive ? 'text-green' : 'text-red'}">${isPositive ? '+' : ''}${percentChange.toFixed(2)}%</td>
                <td>
                    <button class="btn btn-danger" style="padding: 6px 12px; font-size: 12px;" onclick="removeStock('${stock.symbol}')">Remove</button>
                </td>
            </tr>
        `;
    }).join('');
}

// Update the summary cards at the top of the portfolio page
function updatePortfolioSummary() {
    // Calculate totals from current portfolio data
    let totalValue = 0;
    let totalCost = 0;
    let dayGain = 0;

    portfolio.forEach(stock => {
        const marketValue = stock.shares * stock.currentPrice;
        const costBasis = stock.shares * stock.avgPrice;
        const dailyChange = (Math.random() - 0.5) * (stock.currentPrice * 0.02); // simulate daily move

        totalValue += marketValue;
        totalCost += costBasis;
        dayGain += dailyChange * stock.shares;

        // Apply simulated intraday price move
        stock.currentPrice = Math.max(0.01, stock.currentPrice + dailyChange);
    });

    const totalGain = totalValue - totalCost;
    const totalGainPct = totalCost > 0 ? (totalGain / totalCost) * 100 : 0;
    const dayGainPct = totalValue !== 0 ? (dayGain / (totalValue - dayGain)) * 100 : 0;

    // Update Total Value
    const totalValueEl = document.getElementById('portfolio-total-value');
    const totalChangeEl = document.getElementById('portfolio-total-change-text');
    const totalArrowEl = document.getElementById('portfolio-total-arrow');

    if (totalValueEl) {
        totalValueEl.textContent = `$${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (totalChangeEl && totalArrowEl) {
        const sign = totalGain >= 0 ? '+' : '-';
        const absPct = Math.abs(totalGainPct).toFixed(2);
        totalChangeEl.textContent = `${sign}${absPct}% all time`;
        totalArrowEl.textContent = totalGain >= 0 ? '↑' : '↓';
        totalChangeEl.parentElement.classList.toggle('positive', totalGain >= 0);
        totalChangeEl.parentElement.classList.toggle('negative', totalGain < 0);
    }

    // Update Total Gain/Loss
    const totalGainEl = document.getElementById('portfolio-total-gain');
    const totalGainTextEl = document.getElementById('portfolio-total-gain-text');
    const totalGainArrowEl = document.getElementById('portfolio-total-gain-arrow');

    if (totalGainEl) {
        const sign = totalGain >= 0 ? '+' : '-';
        totalGainEl.textContent = `${sign}$${Math.abs(totalGain).toFixed(2)}`;
        totalGainEl.style.color = totalGain >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    }
    if (totalGainTextEl && totalGainArrowEl) {
        const sign = totalGain >= 0 ? '+' : '-';
        const absPct = Math.abs(totalGainPct).toFixed(2);
        totalGainTextEl.textContent = `${sign}${absPct}% all time`;
        totalGainArrowEl.textContent = totalGain >= 0 ? '↑' : '↓';
        totalGainTextEl.parentElement.classList.toggle('positive', totalGain >= 0);
        totalGainTextEl.parentElement.classList.toggle('negative', totalGain < 0);
    }

    // Update Day's Gain/Loss
    const dayGainEl = document.getElementById('portfolio-day-gain');
    const dayGainTextEl = document.getElementById('portfolio-day-gain-text');
    const dayGainArrowEl = document.getElementById('portfolio-day-gain-arrow');

    if (dayGainEl) {
        const sign = dayGain >= 0 ? '+' : '-';
        dayGainEl.textContent = `${sign}$${Math.abs(dayGain).toFixed(2)}`;
        dayGainEl.style.color = dayGain >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    }
    if (dayGainTextEl && dayGainArrowEl) {
        const sign = dayGain >= 0 ? '+' : '-';
        const absPct = Math.abs(dayGainPct).toFixed(2);
        dayGainTextEl.textContent = `${sign}${absPct}% today`;
        dayGainArrowEl.textContent = dayGain >= 0 ? '↑' : '↓';
        dayGainTextEl.parentElement.classList.toggle('positive', dayGain >= 0);
        dayGainTextEl.parentElement.classList.toggle('negative', dayGain < 0);
    }

    // Persist a snapshot so dashboard can show matching stats
    try {
        const snapshot = {
            totalValue,
            totalCost,
            totalGain,
            totalGainPct,
            dayGain,
            dayGainPct,
            updatedAt: new Date().toISOString()
        };
        localStorage.setItem('portfolio_summary', JSON.stringify(snapshot));
    } catch (e) {
        console.warn('Unable to persist portfolio summary snapshot', e);
    }

    // After mutating prices, refresh table and charts to reflect new values
    updatePortfolioTable();
}

// Handle add stock form submission
async function handleAddStock(e) {
    e.preventDefault();
    
    const symbolInput = document.getElementById('stock-symbol');
    const sharesInput = document.getElementById('stock-shares');
    const priceInput = document.getElementById('stock-price');
    
    const symbol = symbolInput.value.toUpperCase();
    const shares = parseFloat(sharesInput.value);
    const price = parseFloat(priceInput.value);
    
    // Validate
    if (!symbol || shares <= 0 || price <= 0) {
        alert('Please enter valid values');
        return;
    }
    
    // Check if stock already exists
    const existingStock = portfolio.find(s => s.symbol === symbol);
    if (existingStock) {
        alert('Stock already in portfolio. Please remove it first.');
        return;
    }
    
    // Simulate fetching stock info
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<div class="spinner"></div>';
    submitBtn.disabled = true;
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Add new stock (mock data)
    const newStock = {
        symbol: symbol,
        name: getCompanyName(symbol),
        shares: shares,
        avgPrice: price,
        currentPrice: price * (1 + (Math.random() - 0.5) * 0.1) // Random current price
    };
    
    portfolio.push(newStock);
    
    // Update UI
    updatePortfolioTable();
    
    // Reinitialize charts
    const allocationChart = Chart.getChart(document.getElementById('allocationChart'));
    if (allocationChart) allocationChart.destroy();
    initAllocationChart();
    if (newsEffectChartInstance) {
        newsEffectChartInstance.destroy();
        newsEffectChartInstance = null;
    }
    cachedNewsImpacts = {};
    initNewsEffectChart();

    // Reset form
    symbolInput.value = '';
    sharesInput.value = '';
    priceInput.value = '';
    
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
    
    // Show success message
    alert(`${symbol} has been added to your portfolio!`);
}

// Fetch live price for a symbol and auto-fill the Purchase Price field
async function fetchAndSetLivePurchasePrice(symbol) {
    const priceInput = document.getElementById('stock-price');
    if (!priceInput) return;

    try {
        const response = await fetch(`/api/prediction/stocks/${symbol}/live/`);
        if (!response.ok) {
            return;
        }
        const payload = await response.json();
        const data = payload && payload.data;
        if (!data || typeof data.price !== 'number') {
            return;
        }
        priceInput.value = data.price.toFixed(2);
    } catch (error) {
        console.error('Failed to fetch live price for', symbol, error);
        // Silent failure: user can still enter price manually
    }
}

// Get company name (mock)
function getCompanyName(symbol) {
    const names = {
        'AAPL': 'Apple Inc.',
        'TSLA': 'Tesla Inc.',
        'GOOGL': 'Alphabet Inc.',
        'MSFT': 'Microsoft Corp.',
        'AMZN': 'Amazon.com Inc.',
        'INFY': 'Infosys Ltd.',
        'META': 'Meta Platforms Inc.',
        'NVDA': 'NVIDIA Corp.',
        'NFLX': 'Netflix Inc.',
        'AMD': 'Advanced Micro Devices'
    };
    return names[symbol] || `${symbol} Corp.`;
}

// Remove stock from portfolio
function removeStock(symbol) {
    if (!confirm(`Are you sure you want to remove ${symbol} from your portfolio?`)) {
        return;
    }
    
    portfolio = portfolio.filter(s => s.symbol !== symbol);

    // Update UI
    updatePortfolioTable();

    // Reinitialize charts
    const allocationChart = Chart.getChart(document.getElementById('allocationChart'));
    if (allocationChart) allocationChart.destroy();
    initAllocationChart();
    if (newsEffectChartInstance) {
        newsEffectChartInstance.destroy();
        newsEffectChartInstance = null;
    }
    cachedNewsImpacts = {};
    initNewsEffectChart();
}

// Calculate portfolio totals
function calculateTotals() {
    let totalValue = 0;
    let totalCost = 0;
    
    portfolio.forEach(stock => {
        totalValue += stock.shares * stock.currentPrice;
        totalCost += stock.shares * stock.avgPrice;
    });
    
    const totalGainLoss = totalValue - totalCost;
    const totalReturn = (totalGainLoss / totalCost) * 100;
    
    return {
        totalValue,
        totalCost,
        totalGainLoss,
        totalReturn
    };
}

// Export portfolio data
function exportPortfolio() {
    const csvContent = [
        ['Symbol', 'Name', 'Shares', 'Avg Price', 'Current Price', 'Market Value', 'Gain/Loss'].join(','),
        ...portfolio.map(s => [
            s.symbol,
            s.name,
            s.shares,
            s.avgPrice,
            s.currentPrice,
            s.shares * s.currentPrice,
            (s.shares * s.currentPrice) - (s.shares * s.avgPrice)
        ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'portfolio.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initAllocationChart,
        initPerformanceChart,
        updatePortfolioTable,
        handleAddStock,
        removeStock,
        calculateTotals
    };
}
