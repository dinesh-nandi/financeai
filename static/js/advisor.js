/**
 * FinanceAI - AI Strategy Advisor Module
 * Handles chat interface and AI responses
 */

// Protect route
if (!isAuthenticated()) {
    window.location.href = '/login/';
}

// Chat state
let chatHistory = [];
let isTyping = false;

// Typing effect configuration
const TYPING_SPEED = 60; // milliseconds per character (60 = slow, 30 = medium, 10 = fast)
const TYPING_ENABLED = true; // Set to false to disable typing effect
const SHOW_TYPING_CURSOR = true; // Show blinking cursor while typing

// AI responses database
const aiResponses = {
    'portfolio': `Based on your current portfolio analysis, here are my recommendations:

**Strengths:**
- Good exposure to tech sector with AAPL and MSFT
- Diversified across multiple industries
- Strong performers showing consistent growth

**Areas for Improvement:**
- Consider adding healthcare stocks for stability
- Your tech allocation (65%) is high - aim for 50-55%
- Add some dividend-paying stocks for income

**Suggested Actions:**
1. Add JNJ or PFE for healthcare exposure
2. Consider VOO or SPY for broad market exposure
3. Look into REITs for real estate diversification`,

    'tech stocks': `Regarding tech stocks in the current market:

**Current Outlook:**
The tech sector is showing mixed signals. While AI-related stocks are booming, traditional tech faces headwinds from interest rates.

**Top Picks:**
- **AAPL** - Strong fundamentals, services growth
- **MSFT** - AI leadership with OpenAI partnership
- **NVDA** - AI chip demand surge
- **GOOGL** - Undervalued, strong cloud growth

**Risk Factors:**
- High valuations in AI stocks
- Regulatory concerns
- Interest rate sensitivity

**Recommendation:** Dollar-cost average into quality names rather than chasing momentum.`,

    'dividend': `Here are some of the best dividend stocks to consider:

**Dividend Aristocrats:**
- **JNJ** - 2.9% yield, 61 years of increases
- **PG** - 2.4% yield, consumer staples stability
- **KO** - 3.1% yield, iconic brand
- **MCD** - 2.2% yield, recession-resistant

**High Yield Options:**
- **VZ** - 6.8% yield, telecom stability
- **XOM** - 3.2% yield, energy recovery
- **ABBV** - 4.1% yield, pharma pipeline

**REITs for Income:**
- **O** - Monthly dividends, retail properties
- **VNQ** - Diversified REIT ETF

**Strategy:** Build a ladder with 40% aristocrats, 40% high yield, 20% REITs.`,

    'diversification': `Here's how to diversify your portfolio effectively:

**Target Allocation (Moderate Risk):**
- US Stocks: 40-50%
- International: 15-20%
- Bonds: 20-25%
- Alternatives: 5-10%

**Sector Breakdown:**
- Technology: 20-25%
- Healthcare: 15-20%
- Financials: 10-15%
- Consumer: 10-15%
- Energy/Utilities: 5-10%
- Other: 10-15%

**Implementation:**
1. Start with broad ETFs (VTI, VXUS, BND)
2. Add sector-specific ETFs for targeted exposure
3. Individual stocks for conviction plays (max 20%)
4. Rebalance quarterly

**Your Current Status:** You're overweight in tech. Consider adding healthcare and international exposure.`,

    'dollar-cost averaging': `Dollar-Cost Averaging (DCA) Explained:

**What is DCA?**
Investing a fixed amount at regular intervals regardless of price, reducing the impact of volatility.

**Benefits:**
- Removes emotion from investing
- Buys more shares when prices are low
- Reduces risk of investing at market peaks
- Builds disciplined investing habits

**Example:**
Instead of investing $12,000 at once, invest $1,000 monthly for 12 months.

**Best Practices:**
1. Set automatic transfers
2. Invest on the same day each month
3. Don't try to time the market
4. Stay consistent during downturns
5. Increase contributions with salary raises

**When to Use:**
- Long-term investing (5+ years)
- Volatile markets
- Building new positions
- Reducing lump-sum risk`,

    'market outlook': `Market Outlook for the Coming Month:

**Macro Factors:**
- Fed likely to maintain higher rates
- Inflation cooling but sticky
- Earnings season showing resilience
- Geopolitical tensions persist

**Technical Analysis:**
- S&P 500 testing resistance at 4,800
- Support at 4,600 level
- VIX elevated but manageable
- Breadth improving

**Sector Rotation:**
- Tech: Consolidating after AI rally
- Healthcare: Defensive appeal
- Energy: Supply concerns support prices
- Financials: Benefiting from higher rates

**AI Prediction:**
60% probability of modest gains (2-4%) with increased volatility. Key catalyst: Fed minutes and jobs data.

**Strategy:** Stay invested, use dips as buying opportunities, maintain cash cushion for volatility.`,

    'risk': `Portfolio Risk Analysis & Management:

**Your Current Risk Profile:**
- Risk Score: 68/100 (Moderate-High)
- Beta: 1.12 (slightly more volatile than market)
- Volatility: 18.5% (above average)

**Key Risks:**
1. **Concentration Risk** - 65% in tech
2. **Sector Risk** - Overexposure to cyclical industries
3. **Single Stock Risk** - Individual names vs ETFs

**Risk Mitigation Strategies:**
1. **Diversification** - Add uncorrelated assets
2. **Position Sizing** - No single stock > 10%
3. **Stop Losses** - Set at -15% for individual stocks
4. **Hedging** - Consider VIX calls or put spreads

**Conservative Adjustments:**
- Reduce tech to 45%
- Add bonds (10-15%)
- Include dividend stocks (20%)
- International diversification (15%)

**Monitoring:** Review monthly, rebalance quarterly.`,

    'default': `Thank you for your question! Based on my analysis of current market conditions and your portfolio, here's what I recommend:

**General Principles:**
1. Stay diversified across sectors and geographies
2. Maintain a long-term perspective
3. Don't try to time the market
4. Regularly rebalance your portfolio
5. Keep an emergency fund separate from investments

**Current Market Context:**
- Interest rates remain elevated
- AI driving tech sector growth
- Inflation showing signs of cooling
- International markets offering value

**For Your Specific Situation:**
I'd need more details about your goals, timeline, and risk tolerance to provide personalized advice. Consider scheduling a comprehensive portfolio review.

Would you like me to analyze a specific aspect of your portfolio or discuss particular investment opportunities?`
};

// Initialize advisor page
document.addEventListener('DOMContentLoaded', function() {
    // Log typing effect configuration
    console.log('%c=== FinanceAI Advisor Typing Effect ===', 'color: #00d4ff; font-weight: bold; font-size: 14px;');
    console.log('%cStatus: ' + (TYPING_ENABLED ? '✅ ENABLED' : '❌ DISABLED'), 'color: ' + (TYPING_ENABLED ? '#10b981' : '#ef4444') + '; font-weight: bold;');
    console.log('%cSpeed: ' + TYPING_SPEED + 'ms per character', 'color: #f59e0b;');
    console.log('%cCursor: ' + (SHOW_TYPING_CURSOR ? '✅ YES' : '❌ NO'), 'color: #8b5cf6;');
    console.log('%c══════════════════════════════════', 'color: #00d4ff;');
    
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.focus();
    }
});

// Handle key press in chat input
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Use suggested prompt
function usePrompt(prompt) {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = prompt;
        chatInput.focus();
        sendMessage();
    }
}

// Send message
async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message || isTyping) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Get AI response
    await getAIResponse(message);
}

// Add message to chat
function addMessage(text, sender) {
    const chatMessages = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = sender === 'ai' ? '🤖' : '👤';
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    
    // Format text with markdown-like syntax
    let formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Use typing effect for AI messages if enabled
    if (sender === 'ai' && TYPING_ENABLED) {
        console.log('✓ Typing effect enabled for AI message');
        addMessageWithTypingEffect(bubble, formattedText);
    } else {
        console.log('✗ Typing effect disabled or not AI sender');
        bubble.innerHTML = formattedText;
    }
    
    // Store in history
    chatHistory.push({ sender, text });
}

// Add message with character-by-character typing effect (line by line)
function addMessageWithTypingEffect(bubbleElement, htmlText) {
    console.log('🎬 addMessageWithTypingEffect called with text:', htmlText.substring(0, 50) + '...');
    
    // Parse HTML to get plain text
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlText;
    const plainText = tempDiv.innerText || tempDiv.textContent || ''; // Fallback to textContent
    
    console.log('📄 Plain text extracted:', plainText.length + ' characters');
    console.log('⚙️ Typing speed:', TYPING_SPEED + 'ms per character');
    
    let charIndex = 0;
    bubbleElement.innerHTML = ''; // Clear the bubble
    
    isTyping = true;
    const startTime = Date.now();
    
    // Simpler typing function - just append text progressively
    const typeInterval = setInterval(() => {
        if (charIndex < plainText.length) {
            // Get the substring of plain text so far
            const currentText = plainText.substring(0, charIndex + 1);
            
            // Apply formatting
            let displayText = currentText
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
            
            // Add cursor
            if (SHOW_TYPING_CURSOR) {
                displayText += '<span class="typing-cursor">|</span>';
            }
            
            bubbleElement.innerHTML = displayText;
            
            // Auto-scroll
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            charIndex++;
        } else {
            // Complete - show full HTML formatted text
            console.log('✅ Typing complete in ' + (Date.now() - startTime) + 'ms');
            bubbleElement.innerHTML = htmlText;
            isTyping = false;
            clearInterval(typeInterval);
            
            // Auto-scroll one final time
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
    }, TYPING_SPEED);
}

// Show typing indicator
function showTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    isTyping = true;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message ai';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="chat-avatar">🤖</div>
        <div class="chat-bubble" style="display: flex; gap: 4px; align-items: center; padding: 16px 20px;">
            <span style="width: 8px; height: 8px; background: var(--text-secondary); border-radius: 50%; animation: bounce 1s infinite;"></span>
            <span style="width: 8px; height: 8px; background: var(--text-secondary); border-radius: 50%; animation: bounce 1s infinite 0.2s;"></span>
            <span style="width: 8px; height: 8px; background: var(--text-secondary); border-radius: 50%; animation: bounce 1s infinite 0.4s;"></span>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    // Don't set isTyping = false here - the typing effect function manages it
}

// Get AI response from backend only (no hard-coded fallbacks)
async function getAIResponse(userMessage) {
    try {
        const response = await fetch('/api/advisor/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage })
        });

        removeTypingIndicator();

        if (response.ok) {
            const payload = await response.json();
            const data = payload && payload.data;
            if (data && data.response) {
                addMessage(data.response, 'ai');
                return;
            }
        } else {
            console.error('Advisor API error status:', response.status);
        }
    } catch (error) {
        console.error('Error getting AI response:', error);
        removeTypingIndicator();
    }

    // If we reach here, backend failed or returned an invalid payload
    addMessage('Sorry, I could not reach the AI advisor service right now.', 'ai');
}

// Clear chat history
function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="chat-message ai">
            <div class="chat-avatar">🤖</div>
            <div class="chat-bubble">
                <p>Chat history cleared. How can I help you today?</p>
            </div>
        </div>
    `;
    chatHistory = [];
}

// Export chat
function exportChat() {
    const chatText = chatHistory.map(msg => `${msg.sender.toUpperCase()}: ${msg.text}`).join('\n\n');
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'financeai-chat.txt';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Add bounce animation for typing indicator
const style = document.createElement('style');
style.textContent = `
    @keyframes bounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        handleKeyPress,
        usePrompt,
        sendMessage,
        addMessage,
        getAIResponse
    };
}
