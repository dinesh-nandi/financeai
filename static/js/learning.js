/**
 * FinanceAI - Learning Module
 * Multi-page articles with reading progress (Page X of Y, % completed)
 */

if (!isAuthenticated()) {
    window.location.href = '/login/';
}

const READING_PROGRESS_KEY = 'learningReadingProgress';

// Topics: each has title, pages (array of { title, content }), and optional quiz
const learningTopics = {
    basics: {
        title: 'Investing Basics',
        pages: [
            {
                title: 'What is a Stock?',
                content: `
                    <h4>What is a Stock?</h4>
                    <p style="margin-bottom: 16px;">
                        A stock, also known as equity, is a security that represents the ownership of a fraction of a corporation.
                        This entitles the owner to a proportion of the corporation's assets and profits equal to how much stock they own.
                        Units of stock are called "shares."
                    </p>
                    <p style="margin-bottom: 16px;">
                        Stocks are bought and sold on exchanges (e.g. NSE, BSE in India; NYSE, NASDAQ in the US). When you buy a share,
                        you become a part-owner of that company and may benefit from price appreciation and dividends.
                    </p>
                `
            },
            {
                title: 'How Do Stocks Work?',
                content: `
                    <h4>How Do Stocks Work?</h4>
                    <p style="margin-bottom: 16px;">
                        When you buy a company's stock, you're purchasing a small piece of that company. Investors buy stocks in companies
                        they believe will grow. If the company does well, the stock price may rise and you can sell for a profit.
                    </p>
                    <p style="margin-bottom: 16px;">
                        Companies issue stock to raise capital. In return, shareholders may receive dividends (a share of profits) and have
                        voting rights on certain company decisions. Stock prices change throughout the trading day based on supply and demand.
                    </p>
                `
            },
            {
                title: 'Key Terms to Know',
                content: `
                    <h4>Key Terms to Know</h4>
                    <ul style="margin-left: 20px; line-height: 1.9;">
                        <li><strong>Market Cap:</strong> The total value of a company's outstanding shares (price × shares). Large-cap, mid-cap, and small-cap refer to company size.</li>
                        <li><strong>Dividend:</strong> A portion of profits paid to shareholders, usually quarterly.</li>
                        <li><strong>IPO:</strong> Initial Public Offering – when a company first sells stock to the public.</li>
                        <li><strong>Bull Market:</strong> A period of rising stock prices and optimism.</li>
                        <li><strong>Bear Market:</strong> A period of falling stock prices and pessimism.</li>
                        <li><strong>Volume:</strong> The number of shares traded in a period; high volume often means more conviction.</li>
                    </ul>
                `
            },
            {
                title: 'Why Invest in Stocks?',
                content: `
                    <h4>Why Invest in Stocks?</h4>
                    <p style="margin-bottom: 16px;">
                        Over the long term, equities have historically outperformed many other assets like bonds or cash. They offer the potential
                        for capital growth and, in some cases, dividend income. That said, stocks are riskier than fixed-income products.
                    </p>
                    <p style="margin-bottom: 16px;">
                        Investing in a diversified set of stocks (or through mutual funds/ETFs) can help spread risk. Starting early and staying
                        invested for years allows compounding to work in your favour. Never invest money you cannot afford to lose.
                    </p>
                `
            },
            {
                title: 'Getting Started',
                content: `
                    <h4>Getting Started</h4>
                    <p style="margin-bottom: 16px;">
                        To start investing you typically need a demat and trading account with a broker. You can place orders to buy or sell
                        during market hours. Many beginners start with index funds or SIPs in mutual funds before picking individual stocks.
                    </p>
                    <p style="margin-bottom: 16px;">
                        Set clear goals (retirement, house, education), define your risk tolerance, and learn the basics of reading financial
                        statements and news. Use this app's Prediction and Portfolio tools to practice and track your learning.
                    </p>
                `
            }
        ],
        quiz: [
            { question: 'What is a stock?', options: ['A type of bond', 'A share of ownership in a company', 'A government security', 'A bank account'], correct: 1 },
            { question: 'What does IPO stand for?', options: ['International Profit Org', 'Initial Public Offering', 'Internal Price Option', 'Investment Portfolio'], correct: 1 },
            { question: 'What is a dividend?', options: ['A chart type', 'Company revenue', 'A portion of profits paid to shareholders', 'New stock price'], correct: 2 }
        ]
    },
    technical: {
        title: 'Technical Analysis',
        pages: [
            { title: 'What is Technical Analysis?', content: '<h4>What is Technical Analysis?</h4><p style="margin-bottom: 16px;">Technical analysis evaluates investments by studying price and volume. Practitioners use charts and indicators to identify trends, support/resistance, and entry/exit points. It assumes price action reflects all information and that patterns repeat.</p>' },
            { title: 'Candlestick Charts', content: '<h4>Candlestick Charts</h4><p style="margin-bottom: 16px;">Candlestick charts show open, high, low, and close. The body is open–close; wicks show high and low. Green usually means up, red means down. Patterns like doji, hammer, and engulfing can suggest reversals.</p>' },
            { title: 'Support and Resistance', content: '<h4>Support and Resistance</h4><p style="margin-bottom: 16px;"><strong>Support</strong> is where buying tends to emerge; <strong>resistance</strong> is where selling appears. Breakouts can lead to follow-through; use volume for confirmation.</p>' },
            { title: 'Moving Averages', content: '<h4>Moving Averages</h4><p style="margin-bottom: 16px;">MAs smooth price over a period (e.g. 50-day, 200-day). Price above MA can mean uptrend; crossovers (e.g. golden cross) are watched for trend changes. They also act as dynamic support/resistance.</p>' },
            { title: 'Volume and Momentum', content: '<h4>Volume and Momentum</h4><p style="margin-bottom: 16px;">Volume shows how many shares traded. High volume on a move adds credibility. RSI and MACD help gauge momentum and overbought/oversold conditions.</p>' }
        ],
        quiz: [
            { question: 'What does technical analysis primarily study?', options: ['Financial statements', 'Price and volume', 'CEO interviews', 'Macro data'], correct: 1 },
            { question: 'What is "support"?', options: ['A resistance level', 'A price level where buying tends to appear', 'A type of chart', 'A moving average'], correct: 1 }
        ]
    },
    portfolio: {
        title: 'Portfolio Management',
        pages: [
            { title: 'Diversification', content: '<h4>Diversification</h4><p style="margin-bottom: 16px;">Diversification means spreading money across assets (stocks, bonds, sectors) to reduce risk. A diversified portfolio can smooth returns compared to holding few names.</p>' },
            { title: 'Asset Allocation', content: '<h4>Asset Allocation</h4><p style="margin-bottom: 16px;">Asset allocation is how you divide the portfolio between stocks, bonds, and cash. It should match goals, time horizon, and risk tolerance.</p>' },
            { title: 'Rebalancing', content: '<h4>Rebalancing</h4><p style="margin-bottom: 16px;">Rebalancing brings the mix back to your target by selling winners and buying underperformers. It enforces discipline; many do it once or twice a year.</p>' },
            { title: 'Risk and Return', content: '<h4>Risk and Return</h4><p style="margin-bottom: 16px;">Higher return usually comes with higher risk. Understand volatility and drawdowns. Use this app\'s Portfolio and Prediction tools to see how choices might behave.</p>' }
        ],
        quiz: [{ question: 'What is diversification?', options: ['Putting all in one stock', 'Spreading investments across assets', 'Only bonds', 'Trading daily'], correct: 1 }]
    },
    risk: {
        title: 'Risk Management',
        pages: [
            { title: 'Understanding Investment Risk', content: '<h4>Understanding Investment Risk</h4><p style="margin-bottom: 16px;">Investment risk is the chance of losing capital. Understand the types of risk, how much you can afford to lose, and how to manage position sizes.</p>' },
            { title: 'Types of Risk', content: '<h4>Types of Risk</h4><ul style="margin-left: 20px; line-height: 1.9;"><li><strong>Market Risk:</strong> Prices fall across the market.</li><li><strong>Liquidity Risk:</strong> Cannot sell quickly at a fair price.</li><li><strong>Credit Risk:</strong> Borrower or issuer defaults.</li><li><strong>Inflation Risk:</strong> Purchasing power erodes.</li><li><strong>Concentration Risk:</strong> Too much in one stock or sector.</li></ul></p>' },
            { title: 'Position Sizing', content: '<h4>Position Sizing</h4><p style="margin-bottom: 16px;">Limit each position to a small % of the portfolio (e.g. 2–5%). Use stop-losses or rules to cut losses. Preserving capital is as important as making gains.</p>' },
            { title: 'Emotional Discipline', content: '<h4>Emotional Discipline</h4><p style="margin-bottom: 16px;">Have a written plan: when to buy, when to sell, how much to risk. Avoid chasing tips or panic-selling. Use Learning and Community in this app to stay informed.</p>' }
        ],
        quiz: [{ question: 'What is market risk?', options: ['Default by a company', 'Risk that markets fall broadly', 'Inflation', 'Low liquidity'], correct: 1 }]
    }
};

let currentTopicKey = null;
let currentPageIndex = 0;
let currentQuiz = null;
let currentQuestionIndex = 0;
let quizAnswers = [];

function getTopic() {
    return currentTopicKey ? learningTopics[currentTopicKey] : null;
}

function getTotalPages() {
    const topic = getTopic();
    return topic && topic.pages ? topic.pages.length : 1;
}

function getReadingProgress() {
    const total = getTotalPages();
    if (total <= 0) return { pageIndex: 0, totalPages: 1, percent: 0 };
    const pageIndex = Math.min(currentPageIndex, total - 1);
    const percent = Math.round(((pageIndex + 1) / total) * 100);
    return { pageIndex, totalPages: total, percent };
}

function saveReadingProgress() {
    if (!currentTopicKey) return;
    try {
        let saved = localStorage.getItem(READING_PROGRESS_KEY);
        saved = saved ? JSON.parse(saved) : {};
        saved[currentTopicKey] = currentPageIndex;
        localStorage.setItem(READING_PROGRESS_KEY, JSON.stringify(saved));
    } catch (e) {}
}

function loadReadingProgress(topicKey) {
    try {
        const saved = localStorage.getItem(READING_PROGRESS_KEY);
        if (!saved) return 0;
        const data = JSON.parse(saved);
        return Math.max(0, parseInt(data[topicKey], 10) || 0);
    } catch (e) { return 0; }
}

function renderPage() {
    const topic = getTopic();
    if (!topic || !topic.pages || !topic.pages.length) return;

    const totalPages = topic.pages.length;
    const page = topic.pages[currentPageIndex];
    if (!page) return;

    const contentTitle = document.getElementById('content-title');
    const contentBody = document.getElementById('content-body');
    const pageIndicator = document.getElementById('content-page-indicator');
    const percentDone = document.getElementById('content-percent-done');
    const progressFill = document.getElementById('content-progress-fill');
    const btnPrev = document.getElementById('btn-prev-page');
    const btnNext = document.getElementById('btn-next-page');
    const btnQuiz = document.getElementById('btn-take-quiz');

    contentTitle.textContent = topic.title + ': ' + page.title;
    contentBody.innerHTML = page.content;

    const progress = getReadingProgress();
    if (pageIndicator) pageIndicator.textContent = 'Page ' + (progress.pageIndex + 1) + ' of ' + progress.totalPages;
    if (percentDone) percentDone.textContent = progress.percent + '% completed';
    if (progressFill) progressFill.style.width = progress.percent + '%';

    if (btnPrev) btnPrev.style.display = currentPageIndex > 0 ? 'inline-flex' : 'none';
    if (btnNext) btnNext.style.display = currentPageIndex < totalPages - 1 ? 'inline-flex' : 'none';
    if (btnQuiz) btnQuiz.style.display = currentPageIndex === totalPages - 1 ? 'inline-flex' : 'none';

    saveReadingProgress();
}

function showTopic(topicKey) {
    if (!learningTopics[topicKey]) return;

    currentTopicKey = topicKey;
    currentPageIndex = loadReadingProgress(topicKey);
    const topic = learningTopics[topicKey];
    if (topic.pages && currentPageIndex >= topic.pages.length) {
        currentPageIndex = topic.pages.length - 1;
    }

    currentQuiz = topic.quiz || [];
    currentQuestionIndex = 0;
    quizAnswers = [];

    const contentSection = document.getElementById('content-section');
    contentSection.style.display = 'block';
    renderPage();
    contentSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function prevPage() {
    if (currentPageIndex <= 0) return;
    currentPageIndex--;
    renderPage();
    document.getElementById('content-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function nextPage() {
    const total = getTotalPages();
    if (currentPageIndex >= total - 1) return;
    currentPageIndex++;
    renderPage();
    document.getElementById('content-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeContent() {
    document.getElementById('content-section').style.display = 'none';
}

function startQuiz() {
    if (!currentQuiz || currentQuiz.length === 0) {
        alert('No quiz available for this topic.');
        return;
    }
    const quizSection = document.getElementById('quiz-section');
    const contentSection = document.getElementById('content-section');
    contentSection.style.display = 'none';
    quizSection.style.display = 'block';
    currentQuestionIndex = 0;
    quizAnswers = [];
    showQuestion();
}

function showQuestion() {
    const question = currentQuiz[currentQuestionIndex];
    const quizProgress = document.getElementById('quiz-progress');
    const quizQuestion = document.getElementById('quiz-question');
    if (!quizProgress || !quizQuestion) return;

    quizProgress.textContent = 'Question ' + (currentQuestionIndex + 1) + ' of ' + currentQuiz.length;

    const optionsHtml = question.options.map(function (opt, index) {
        return '<label style="display: flex; align-items: center; gap: 12px; padding: 16px; background: var(--bg-glass); border: 1px solid var(--border-color); border-radius: var(--radius-md); cursor: pointer; transition: var(--transition);" class="quiz-option" onclick="selectOption(' + index + ')">' +
            '<input type="radio" name="quiz" value="' + index + '" style="width: 18px; height: 18px;">' +
            '<span>' + opt + '</span></label>';
    }).join('');

    quizQuestion.innerHTML = '<p style="font-size: 18px; margin-bottom: 20px;">' + question.question + '</p>' +
        '<div style="display: flex; flex-direction: column; gap: 12px;">' + optionsHtml + '</div>';
}

function selectOption(index) {
    quizAnswers[currentQuestionIndex] = index;
    const options = document.querySelectorAll('.quiz-option');
    options.forEach(function (opt, i) {
        opt.style.borderColor = i === index ? 'var(--accent-cyan)' : 'var(--border-color)';
        opt.style.background = i === index ? 'rgba(0, 212, 255, 0.1)' : 'var(--bg-glass)';
    });
}

function nextQuestion() {
    if (quizAnswers[currentQuestionIndex] === undefined) {
        alert('Please select an answer.');
        return;
    }
    currentQuestionIndex++;
    if (currentQuestionIndex >= currentQuiz.length) {
        showQuizResults();
    } else {
        showQuestion();
    }
}

function showQuizResults() {
    const quizSection = document.getElementById('quiz-section');
    let correct = 0;
    currentQuiz.forEach(function (q, i) {
        if (quizAnswers[i] === q.correct) correct++;
    });
    const percentage = currentQuiz.length ? Math.round((correct / currentQuiz.length) * 100) : 0;
    quizSection.innerHTML = '<div style="text-align: center; padding: 40px;">' +
        '<div style="font-size: 64px; margin-bottom: 20px;">' + (percentage >= 70 ? '🎉' : percentage >= 50 ? '👍' : '📚') + '</div>' +
        '<h3 style="margin-bottom: 16px;">Quiz Complete!</h3>' +
        '<p style="font-size: 18px; color: var(--text-secondary); margin-bottom: 24px;">You scored <span style="color: var(--accent-cyan); font-weight: 700;">' + correct + '/' + currentQuiz.length + '</span> (' + percentage + '%)</p>' +
        '<div style="display: flex; gap: 16px; justify-content: center;">' +
        '<button class="btn btn-primary" onclick="retakeQuiz()">Retake Quiz</button>' +
        '<button class="btn btn-secondary" onclick="closeQuiz()">Close</button></div></div>';
    if (percentage >= 70) updateLearningProgress();
}

function retakeQuiz() {
    const quizSection = document.getElementById('quiz-section');
    quizSection.innerHTML = '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">' +
        '<h3>Knowledge Check</h3><span id="quiz-progress" style="color: var(--text-secondary); font-size: 14px;">Question 1 of ' + currentQuiz.length + '</span></div>' +
        '<div id="quiz-question" style="margin-bottom: 24px;"></div>' +
        '<div style="display: flex; justify-content: space-between;">' +
        '<button class="btn btn-secondary" onclick="closeQuiz()">Skip Quiz</button>' +
        '<button class="btn btn-primary" onclick="nextQuestion()">Next Question</button></div>';
    currentQuestionIndex = 0;
    quizAnswers = [];
    showQuestion();
}

function closeQuiz() {
    const quizSection = document.getElementById('quiz-section');
    quizSection.style.display = 'none';
    quizSection.innerHTML = '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">' +
        '<h3>Knowledge Check</h3><span id="quiz-progress" style="color: var(--text-secondary); font-size: 14px;">Question 1 of 5</span></div>' +
        '<div id="quiz-question" style="margin-bottom: 24px;"></div>' +
        '<div style="display: flex; justify-content: space-between;">' +
        '<button class="btn btn-secondary" onclick="closeQuiz()">Skip Quiz</button>' +
        '<button class="btn btn-primary" onclick="nextQuestion()">Next Question</button></div>';
}

function loadLearningProgress() {
    try {
        const progress = localStorage.getItem('learningProgress');
        if (progress) JSON.parse(progress);
    } catch (e) {}
}

function updateLearningProgress() {
    let progress = localStorage.getItem('learningProgress');
    progress = progress ? JSON.parse(progress) : { completed: [], total: 24 };
    if (currentTopicKey && progress.completed.indexOf(currentTopicKey) === -1) {
        progress.completed.push(currentTopicKey);
    }
    localStorage.setItem('learningProgress', JSON.stringify(progress));
}

document.addEventListener('DOMContentLoaded', loadLearningProgress);

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { showTopic, closeContent, prevPage, nextPage, startQuiz, nextQuestion, closeQuiz };
}
