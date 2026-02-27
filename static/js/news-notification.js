/**
 * FinanceAI - Live news notification popup + news ticker line
 * Polls /api/news/live/ every 45s; shows a toast with a different article each time (rotates through list).
 * Also renders a news ticker line that cycles through headlines.
 */
(function () {
    const POLL_INTERVAL_MS = 30000;  // check every 30 seconds
    const TOAST_DURATION_MS = 10000; // vanish after 10 seconds
    const TICKER_CYCLE_MS = 6000;    // change ticker headline every 6s
    function getNewsApiUrl() {
        try {
            var base = (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : '';
            return (base + '/api/news/live/').replace(/([^:]\/)\/+/g, '$1');
        } catch (e) { return '/api/news/live/'; }
    }
    const VANISH_ANIMATION_MS = 350;

    let lastArticles = [];
    let nextShowIndex = 0;   // serial rotation: 0, 1, 2, ... then wrap
    let pollTimer = null;
    let toastTimer = null;
    let tickerIndex = 0;
    let tickerCycleTimer = null;

    function getContainer() {
        let el = document.getElementById('news-notification-container');
        if (!el) {
            el = document.createElement('div');
            el.id = 'news-notification-container';
            el.setAttribute('aria-live', 'polite');
            document.body.appendChild(el);
        }
        return el;
    }

    function getTickerContainer() {
        let el = document.getElementById('news-ticker-line');
        if (!el) {
            el = document.createElement('div');
            el.id = 'news-ticker-line';
            el.setAttribute('aria-label', 'Live news headlines');
            document.body.insertBefore(el, document.body.firstChild);
            document.body.classList.add('has-news-ticker');
        }
        return el;
    }

    function escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showToast(article) {
        const container = getContainer();
        if (toastTimer) clearTimeout(toastTimer);
        container.innerHTML = '';
        const title = article && article.title ? article.title : 'New article published';
        const url = article && article.url ? article.url : '';
        const sourceLabel = article && article.source ? escapeHtml(article.source) : '';
        const impact = (article && article.impact) ? String(article.impact).toLowerCase() : '';
        const impactLabel = impact === 'high' ? 'High' : (impact === 'med' ? 'Med' : (impact === 'low' ? 'Low' : ''));
        const ledClass = impact === 'high' ? 'led-dot-led-hard' : (impact === 'med' ? 'led-dot-led-med' : (impact === 'low' ? 'led-dot-led-easy' : ''));
        let dateTimeStr = '';
        if (article && article.published_at) {
            try {
                const d = new Date(article.published_at);
                if (!isNaN(d.getTime())) {
                    dateTimeStr = d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST';
                }
            } catch (e) {}
        }
        if (!dateTimeStr) {
            const now = new Date();
            const hour = Math.floor(Math.random() * 18) + 6;
            const minute = Math.floor(Math.random() * 60);
            const d = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hour, minute);
            dateTimeStr = d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true }) + ' IST';
        }

        const toast = document.createElement('div');
        toast.className = 'news-notification-toast';
        toast.innerHTML = `
            <div class="news-notification-toast-header">
                <span class="news-notification-toast-icon">📰</span>
                <span class="news-notification-toast-label">${sourceLabel || 'Latest live news'}</span>
                ${impactLabel && ledClass ? `<span class="led-indicator"><span class="led-dot ${ledClass}"></span>${impactLabel}</span>` : ''}
                <span class="news-toast-datetime">${escapeHtml(dateTimeStr)}</span>
                <button type="button" class="news-notification-toast-close" aria-label="Close">&times;</button>
            </div>
            <div class="news-notification-toast-body">
                <div class="news-notification-toast-title">${escapeHtml(title)}</div>
                ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="news-notification-toast-link">Read more →</a>` : ''}
            </div>
        `;
        container.appendChild(toast);

        requestAnimationFrame(function () {
            toast.classList.add('news-notification-toast-visible');
        });

        toast.querySelector('.news-notification-toast-close').addEventListener('click', function () {
            hideToast(container);
        });
        toastTimer = setTimeout(function () {
            hideToast(container);
        }, TOAST_DURATION_MS);
    }

    function hideToast(container) {
        if (toastTimer) {
            clearTimeout(toastTimer);
            toastTimer = null;
        }
        if (!container) container = document.getElementById('news-notification-container');
        const toast = container && container.querySelector('.news-notification-toast');
        if (toast) {
            toast.classList.remove('news-notification-toast-visible');
            toast.classList.add('news-notification-toast-hiding');
            setTimeout(function () {
                toast.remove();
            }, VANISH_ANIMATION_MS);
        }
    }

    /** Filter to articles that have a title (and optionally url) */
    function validArticles(articles) {
        if (!Array.isArray(articles)) return [];
        return articles.filter(function (a) {
            return a && (a.title || '').trim().length > 0;
        });
    }

    /** Pick next article for the popup: one by one serially (0, 1, 2, ... wrap) */
    function pickNextArticle(articles) {
        var list = validArticles(articles);
        if (list.length === 0) return null;
        var idx = nextShowIndex % list.length;
        var chosen = list[idx];
        nextShowIndex = (nextShowIndex + 1) % list.length;
        return chosen;
    }

    /** Update the news ticker line with current list; cycle through headlines */
    function updateTicker(articles) {
        var list = validArticles(articles);
        var container = getTickerContainer();
        if (list.length === 0) {
            container.innerHTML = '<span class="news-ticker-item">No headlines available</span>';
            container.classList.remove('news-ticker-has-items');
            document.body.classList.remove('has-news-ticker');
            return;
        }
        document.body.classList.add('has-news-ticker');
        container.classList.add('news-ticker-has-items');
        container.innerHTML = list.map(function (a, i) {
            var title = (a.title || '').trim();
            var url = a.url || '#';
            var source = a.source ? ' · ' + escapeHtml(a.source) : '';
            return '<a href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer" class="news-ticker-item' + (i === 0 ? ' news-ticker-active' : '') + '" data-index="' + i + '">' + escapeHtml(title) + source + '</a>';
        }).join('');

        if (tickerCycleTimer) clearInterval(tickerCycleTimer);
        tickerIndex = 0;
        var items = container.querySelectorAll('.news-ticker-item');
        if (items.length <= 1) return;

        tickerCycleTimer = setInterval(function () {
            items[tickerIndex].classList.remove('news-ticker-active');
            tickerIndex = (tickerIndex + 1) % items.length;
            items[tickerIndex].classList.add('news-ticker-active');
        }, TICKER_CYCLE_MS);
    }

    async function checkForNewNews() {
        try {
            const url = getNewsApiUrl();
            const res = await fetch(url, { credentials: 'same-origin' });
            if (!res.ok) return;
            const data = await res.json();
            const articles = data && data.data && (data.data.articles || []);
            if (!Array.isArray(articles)) return;

            var list = validArticles(articles);
            if (list.length === 0) return;

            lastArticles = list;
            // Ticker line above header disabled — only show popup toast

            // Each popup: show a different article (rotate through the list)
            var article = pickNextArticle(list);
            if (article) {
                showToast(article);
            }
        } catch (e) {
            console.warn('News notification poll failed', e);
        }
    }

    function startPolling() {
        if (pollTimer) return;
        setTimeout(function () {
            checkForNewNews();
        }, 1500);
        pollTimer = setInterval(checkForNewNews, POLL_INTERVAL_MS);
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
        if (tickerCycleTimer) {
            clearInterval(tickerCycleTimer);
            tickerCycleTimer = null;
        }
    }

    function shouldStart() {
        try {
            if (typeof isAuthenticated === 'function') return isAuthenticated();
        } catch (e) {}
        return true;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            if (shouldStart()) startPolling();
        });
    } else {
        if (shouldStart()) startPolling();
    }
})();
