/**
 * FinanceAI - Community Feed
 * Simple Twitter-style feed (local to this browser) for investors, traders, and experts.
 */

// Require login
if (!isAuthenticated()) {
    window.location.href = '/login/';
}

const STORAGE_KEY = 'community_posts';

// Helper for consistent timestamps in default posts
const _base = Date.now();
function _t(h, m) { return _base - ((h || 0) * 60 + (m || 0)) * 60 * 1000; }

// Default hard-coded community posts shown when there is no local data yet.
const DEFAULT_COMMUNITY_POSTS = [
    {
        id: Date.now() - 1000 * 60 * 60 * 5,
        author: 'Rohan (Swing Trader)',
        text: '📺 Just watched the 9PM finance telecast on CNBC.\n\nKey takeaways:\n- NIFTY support at 22,000, resistance near 22,450\n- Bank stocks still look strong on weekly charts\n- Anchor kept warning about over-leverage – absolutely agree!\n\nI am tightening my stop losses this week and avoiding FOMO entries.',
        imageData: null,
        likes: 42,
        shares: 7,
        comments: [
            {
                author: 'Kavya (Long-term)',
                text: 'Loved that segment too. I am still holding my index funds and ignoring the noise.',
                createdAt: Date.now() - 1000 * 60 * 60 * 4
            },
            {
                author: 'Amit',
                text: 'Same view on FOMO – telecasts can be hype machines if we are not careful.',
                createdAt: Date.now() - 1000 * 60 * 60 * 3
            },
            {
                author: 'Sneha',
                text: 'Which bank names are you watching? I am looking at HDFC and ICICI for swing.',
                createdAt: Date.now() - 1000 * 60 * 60 * 2
            }
        ],
        createdAt: Date.now() - 1000 * 60 * 60 * 5
    },
    {
        id: Date.now() - 1000 * 60 * 60 * 2,
        author: 'Meera (Options Trader)',
        text: 'Today\'s evening finance telecast was super bearish on IT stocks.\n\nPersonally I am seeing decent support on weekly charts and building a small position via SIP instead of lump sum.\n\nTelevision views are useful, but I always double-check with my own risk plan.',
        imageData: null,
        likes: 31,
        shares: 4,
        comments: [
            {
                author: 'Rahul',
                text: 'Fully agree. TV anchors changed their view 3 times this month on IT.',
                createdAt: Date.now() - 1000 * 60 * 60 * 1.5
            },
            {
                author: 'Vikram',
                text: 'Which IT names are in your SIP? TCS and Infosys?',
                createdAt: Date.now() - 1000 * 60 * 60 * 1.2
            },
            {
                author: 'Meera (Options Trader)',
                text: 'Yes, 50% TCS 50% Infy. Small monthly amount only.',
                createdAt: Date.now() - 1000 * 60 * 60 * 1
            }
        ],
        createdAt: Date.now() - 1000 * 60 * 60 * 2
    },
    {
        id: Date.now() - 1000 * 60 * 30,
        author: 'Ananya',
        text: 'Quick summary from today’s market telecast:\n\n- Midcap index looks stretched, but quality names still fine for 5+ years\n- Anchor showed how small SIPs over 10 years beat most \"hot tips\"\n\nMy rule after watching any finance show: never place an order immediately. Sleep over it. 😄',
        imageData: null,
        likes: 58,
        shares: 10,
        comments: [
            {
                author: 'Vikram',
                text: 'That SIP example was a big eye-opener for me.',
                createdAt: Date.now() - 1000 * 60 * 20
            },
            {
                author: 'Priya',
                text: 'Love your rule about not placing orders right after a show.',
                createdAt: Date.now() - 1000 * 60 * 10
            },
            {
                author: 'Ravi',
                text: 'Same here. I keep a 24hr cooling-off for any tip from TV.',
                createdAt: Date.now() - 1000 * 60 * 5
            }
        ],
        createdAt: Date.now() - 1000 * 60 * 30
    },
    {
        id: Date.now() - 1000 * 60 * 15,
        author: 'Sanjay (Positional Trader)',
        text: 'Watched today’s pre‑market telecast on ET Now.\n\nThey highlighted heavy delivery volumes in PSU banks and auto stocks.\n\nI am building a watchlist from that segment but will only enter on my own technical confirmation – TV is just a starting point, not a trading signal.',
        imageData: null,
        likes: 19,
        shares: 3,
        comments: [
            {
                author: 'Deepa',
                text: 'Exactly. I treat those shows as idea generators only.',
                createdAt: Date.now() - 1000 * 60 * 12
            },
            {
                author: 'Kiran',
                text: 'Which PSU banks are on your list? SBI and PNB?',
                createdAt: Date.now() - 1000 * 60 * 10
            }
        ],
        createdAt: Date.now() - 1000 * 60 * 15
    },
    {
        id: Date.now() - 1000 * 60 * 8,
        author: 'Arjun (Beginner)',
        text: 'First time I followed a finance telecast end‑to‑end today.\n\nFelt a bit overwhelmed with all the jargon, but the SIP vs lump‑sum explanation was very helpful.\n\nI have decided to start a small monthly SIP instead of chasing intraday calls.',
        imageData: null,
        likes: 67,
        shares: 9,
        comments: [
            {
                author: 'MentorBot',
                text: 'Great decision. Consistent SIPs + patience usually beat TV tips over the long term.',
                createdAt: Date.now() - 1000 * 60 * 5
            },
            {
                author: 'Lakshmi',
                text: 'Welcome to the club! Start small and increase as you learn.',
                createdAt: Date.now() - 1000 * 60 * 3
            }
        ],
        createdAt: Date.now() - 1000 * 60 * 8
    },
    {
        id: Date.now() - 1000 * 60 * 3,
        author: 'Neha (Fundamental Investor)',
        text: 'Tonight’s fundamental analysis telecast focused on FMCG and pharma valuations.\n\nMost picks looked fully priced to me.\n\nMy takeaway: in bull markets even “defensive” sectors can get expensive – so I am sticking to staggered buying and strict allocation limits.',
        imageData: null,
        likes: 24,
        shares: 6,
        comments: [
            {
                author: 'Aditya',
                text: 'Which FMCG names did they discuss? HUL, Nestle?',
                createdAt: Date.now() - 1000 * 60 * 2
            },
            {
                author: 'Neha (Fundamental Investor)',
                text: 'Yes, both. Also Dabur and Britannia. All trading above my comfort zone.',
                createdAt: Date.now() - 1000 * 60 * 1
            }
        ],
        createdAt: Date.now() - 1000 * 60 * 3
    },
    {
        id: _t(2, 30),
        author: 'Raj (Tech Analyst)',
        text: 'Anyone else using the Prediction tab here for swing ideas? I compared AI view with my own chart reading – pretty aligned on AAPL for the week. Not a recommendation, just sharing. 👍',
        imageData: null,
        likes: 38,
        shares: 5,
        comments: [
            { author: 'Pooja', text: 'I use it for confirmation too. Helps me avoid overtrading.', createdAt: _t(2, 10) },
            { author: 'Karan', text: 'Same. I only take trades when my analysis + AI direction match.', createdAt: _t(1, 55) },
            { author: 'Divya', text: 'Do you use the backtest feature? Found it useful for testing MA crossover.', createdAt: _t(1, 30) }
        ],
        createdAt: _t(2, 30)
    },
    {
        id: _t(1, 50),
        author: 'Suresh (Retired)',
        text: 'Portfolio page – the "after news effect" chart is a nice touch. Reminds me to not panic on headlines. My equity curve would have been much smoother if I had ignored 50% of the news in the last decade. 😅',
        imageData: null,
        likes: 89,
        shares: 12,
        comments: [
            { author: 'Anita', text: 'So true. News creates noise. Discipline beats news every time.', createdAt: _t(1, 30) },
            { author: 'Manoj', text: 'Which time frame do you use on that chart – 1M or 6M?', createdAt: _t(1, 15) },
            { author: 'Suresh (Retired)', text: 'I keep it on 3M. Good balance of detail and trend.', createdAt: _t(1, 0) }
        ],
        createdAt: _t(1, 50)
    },
    {
        id: _t(1, 10),
        author: 'Isha (Learning Mode)',
        text: 'Just finished the "Risk & Reward" module in Learning. The quiz was tougher than I thought! Anyone else found the compound interest examples super motivating? 📚',
        imageData: null,
        likes: 44,
        shares: 2,
        comments: [
            { author: 'Rahul', text: 'Yes! That module changed how I look at small monthly savings.', createdAt: _t(0, 55) },
            { author: 'MentorBot', text: 'Great to hear. Try the "Technical Basics" next if you haven\'t.', createdAt: _t(0, 40) },
            { author: 'Isha (Learning Mode)', text: 'Will do, thanks!', createdAt: _t(0, 25) }
        ],
        createdAt: _t(1, 10)
    },
    {
        id: _t(0, 45),
        author: 'Varun (Crypto + Equity)',
        text: 'Market sentiment on News tab is "Neutral" today. I use it as a filter – only add to positions when sentiment is not extreme. Not foolproof but reduces emotional decisions.',
        imageData: null,
        likes: 27,
        shares: 4,
        comments: [
            { author: 'Aarti', text: 'Same strategy. I avoid big buys when sentiment is too greedy.', createdAt: _t(0, 30) },
            { author: 'Nikhil', text: 'Where exactly do you see that on the News page?', createdAt: _t(0, 18) },
            { author: 'Varun (Crypto + Equity)', text: 'Top of the news cards – there\'s a small sentiment label. Check filters too.', createdAt: _t(0, 5) }
        ],
        createdAt: _t(0, 45)
    },
    {
        id: _t(0, 25),
        author: 'Preeti (Advisor User)',
        text: 'Asked the AI Advisor about "best time to invest a lump sum" – got a clear answer with pros/cons. No fluff. Loving this app for learning without the sales pitch. 🤖',
        imageData: null,
        likes: 61,
        shares: 8,
        comments: [
            { author: 'Gaurav', text: 'I asked about sector rotation. Response was detailed and neutral.', createdAt: _t(0, 15) },
            { author: 'Preeti (Advisor User)', text: 'Right? Feels like having a patient mentor.', createdAt: _t(0, 8) }
        ],
        createdAt: _t(0, 25)
    },
    {
        id: _t(0, 12),
        author: 'Yash (Day Trader)',
        text: 'Quick tip: I keep Prediction + News open on two tabs. When a stock I follow appears in news and AI prediction aligns, I add it to watchlist. No direct trades from it – just better context.',
        imageData: null,
        likes: 33,
        shares: 6,
        comments: [
            { author: 'Tanvi', text: 'Smart workflow. I do the same with Portfolio for tracking.', createdAt: _t(0, 5) }
        ],
        createdAt: _t(0, 12)
    }
];

function loadCommunityPosts() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) {
            // First-time users see default hard-coded posts.
            return DEFAULT_COMMUNITY_POSTS.slice();
        }
        const parsed = JSON.parse(raw);
        // If storage is empty or corrupted, fall back to defaults.
        return Array.isArray(parsed) && parsed.length ? parsed : DEFAULT_COMMUNITY_POSTS.slice();
    } catch (e) {
        console.warn('Failed to parse community posts', e);
        // On any error, fall back to defaults so the feed is never empty.
        return DEFAULT_COMMUNITY_POSTS.slice();
    }
}

function saveCommunityPosts(posts) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(posts));
    } catch (e) {
        console.warn('Failed to save community posts', e);
    }
}

let communityPosts = loadCommunityPosts();

function renderCommunityFeed() {
    const container = document.getElementById('community-feed-list');
    if (!container) return;

    if (!communityPosts.length) {
        container.innerHTML = `
            <p style="color: var(--text-secondary); font-size: 14px;">
                No posts yet. Be the first to share your market view!
            </p>
        `;
        return;
    }

    container.innerHTML = communityPosts
        .sort((a, b) => b.createdAt - a.createdAt)
        .map((post, index) => {
            const date = new Date(post.createdAt);
            const when = date.toLocaleString('en-IN', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
            const likes = post.likes || 0;
            const comments = post.comments ? post.comments.length : 0;
            const shares = post.shares || 0;
            const imageHtml = post.imageData
                ? `<div class="community-post-image-wrap"><img src="${post.imageData}" alt="Post image"></div>`
                : '';
            return `
                <article class="community-post" data-index="${index}">
                    <div class="community-post-header">
                        <div class="community-avatar-small">👤</div>
                        <div>
                            <div class="community-post-author">${post.author || 'Member'}</div>
                            <div class="community-post-meta">${when}</div>
                        </div>
                    </div>
                    <div class="community-post-body">
                        <p>${(post.text || '').replace(/\n/g, '<br>')}</p>
                        ${imageHtml}
                    </div>
                    <div class="community-post-actions">
                        <button class="community-action-btn" data-action="like">
                            ❤️ <span>${likes}</span>
                        </button>
                        <button class="community-action-btn" data-action="comment">
                            💬 <span>${comments}</span>
                        </button>
                        <button class="community-action-btn" data-action="share">
                            🔁 <span>${shares}</span>
                        </button>
                    </div>
                    <div class="community-comments">
                        ${(post.comments || [])
                            .map(c => `<div class="community-comment"><span class="community-comment-author">${c.author || 'User'}:</span> ${c.text}</div>`)
                            .join('')}
                        <div class="community-comment-form">
                            <input type="text" class="form-input community-comment-input" placeholder="Add a comment...">
                            <button class="btn btn-secondary btn-small" data-action="add-comment">Post</button>
                        </div>
                    </div>
                </article>
            `;
        })
        .join('');
}

function initCommunity() {
    const user = getCurrentUser();
    const nameEl = document.getElementById('community-user-name');
    if (nameEl && user) {
        nameEl.textContent = user.name || user.username || 'Share your thoughts';
    }

    const postBtn = document.getElementById('community-post-btn');
    const textEl = document.getElementById('community-post-text');
    const imageInput = document.getElementById('community-post-image');

    if (postBtn && textEl) {
        postBtn.addEventListener('click', async function () {
            const text = textEl.value.trim();
            if (!text) {
                alert('Please write something before posting.');
                return;
            }

            let imageData = null;
            if (imageInput && imageInput.files && imageInput.files[0]) {
                const file = imageInput.files[0];
                if (file.size > 3 * 1024 * 1024) {
                    alert('Image is too large (max 3MB).');
                    return;
                }
                imageData = await new Promise(resolve => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.onerror = () => resolve(null);
                    reader.readAsDataURL(file);
                });
            }

            const newPost = {
                id: Date.now(),
                author: (user && (user.name || user.username)) || 'Member',
                text,
                imageData,
                likes: 0,
                shares: 0,
                comments: [],
                createdAt: Date.now()
            };

            communityPosts.push(newPost);
            saveCommunityPosts(communityPosts);
            textEl.value = '';
            if (imageInput) imageInput.value = '';
            renderCommunityFeed();
        });
    }

    const feed = document.getElementById('community-feed-list');
    if (feed) {
        feed.addEventListener('click', function (e) {
            const btn = e.target.closest('button');
            if (!btn) return;
            const article = e.target.closest('.community-post');
            if (!article) return;
            const index = Number(article.getAttribute('data-index') || '0');
            const post = communityPosts[index];
            if (!post) return;

            const action = btn.getAttribute('data-action');
            if (action === 'like') {
                post.likes = (post.likes || 0) + 1;
            } else if (action === 'share') {
                post.shares = (post.shares || 0) + 1;
                try {
                    navigator.clipboard && navigator.clipboard.writeText(post.text || '');
                } catch (e) {
                    // ignore
                }
            } else if (action === 'add-comment') {
                const input = article.querySelector('.community-comment-input');
                if (!input) return;
                const text = input.value.trim();
                if (!text) return;
                post.comments = post.comments || [];
                post.comments.push({
                    text,
                    author: (user && (user.name || user.username)) || 'User',
                    createdAt: Date.now()
                });
                input.value = '';
            }

            saveCommunityPosts(communityPosts);
            renderCommunityFeed();
        });
    }

    renderCommunityFeed();
}

document.addEventListener('DOMContentLoaded', initCommunity);

