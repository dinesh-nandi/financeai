"""
Advisor views for FinanceAI
"""
import os
import random
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Count

from .models import ChatSession, ChatMessage, InvestmentRecommendation, PortfolioReport, SuggestedPrompt
from .serializers import (
    ChatSessionSerializer, ChatMessageSerializer, ChatRequestSerializer,
    InvestmentRecommendationSerializer, PortfolioReportSerializer,
    SuggestedPromptSerializer, AdvisorStatsSerializer
)

GEMINI_CHAT_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def call_llm_with_context(message: str, portfolio_value: float, holdings_summary: str, prediction_accuracy: float):
    """
    Call Gemini to generate an advisor response.

    Returns the model's text response, or None if not configured / fails.
    """
    # Use the Gemini API key only; other keys (like OpenAI) are not valid here
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None

    system_instruction = (
        "You are a helpful AI financial advisor. Your job is to answer EVERY question the user asks in detail. "
        "Give elaborate, thorough answers: 250–400 words (or more if the question needs it). "
        "Use 4–6 paragraphs or detailed bullet points. Cover context, key points, pros/cons, risks, and practical takeaways. "
        "For stocks or companies: include business overview, sector, what to watch (metrics), and risks. "
        "For concepts (SIP, P/E, diversification): explain clearly with examples. "
        "Never give only a short 1–2 sentence reply; always elaborate. Never reply with only a menu of topics. "
        "If the question is off-topic, give a brief polite answer and suggest they ask about investing. "
        "Never stop mid-sentence. End with a brief note that this is educational, not personalized investment advice."
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "parts": [
                    {"text": message}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.2,
        },
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            GEMINI_CHAT_URL,
            params={"key": api_key},
            json=payload,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]

        return None
    except Exception:
        # Fail silently and let the rule-based fallback handle the response
        return None


class ChatSessionListView(generics.ListAPIView):
    """List user's chat sessions"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user, is_active=True)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()[:20]
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class ChatSessionDetailView(generics.RetrieveAPIView):
    """Get chat session details with messages"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_view(request):
    """Process chat message and return AI response"""
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    message = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id')
    
    # Get or create session (bind to user if authenticated, otherwise anonymous)
    user = request.user if request.user.is_authenticated else None
    if user and session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(
                user=user,
                title=message[:50],
                session_type='general'
            )
    elif user:
        session = ChatSession.objects.create(
            user=user,
            title=message[:50],
            session_type='general'
        )
    else:
        # Anonymous session is not persisted to DB
        session = None
    
    # Save user message
    if session:
        ChatMessage.objects.create(
            session=session,
            sender='user',
            content=message
        )
    
    # Generate AI response
    ai_response = generate_ai_response(user, message, session)
    
    # Save AI message
    if session:
        ChatMessage.objects.create(
            session=session,
            sender='ai',
            content=ai_response['response'],
            metadata={'suggested_followups': ai_response['suggested_followups']}
        )
    
    return Response({
        'status': 'success',
        'data': {
            'response': ai_response['response'],
            'session_id': session.id if session else None,
            'suggested_followups': ai_response['suggested_followups']
        }
    })


def generate_ai_response(user, message, session):
    """
    Generate AI response: try Gemini first so ANY question gets an answer, then fall back to rules.
    """
    message_lower = message.lower()

    from portfolio.models import Portfolio
    from prediction.models import Prediction

    holdings = Portfolio.objects.filter(user=user) if user and user.is_authenticated else []
    portfolio_value = sum(h.current_value for h in holdings) if holdings else 0

    predictions = Prediction.objects.filter(user=user) if user and user.is_authenticated else []
    prediction_accuracy = 0
    if predictions:
        correct = predictions.filter(is_correct=True).count()
        total = predictions.count()
        prediction_accuracy = round((correct / total) * 100, 2) if total > 0 else 0

    holdings_symbols = [h.stock.symbol for h in holdings] if holdings else []
    holdings_summary = ", ".join(holdings_symbols)

    # Try Gemini first so the bot can answer ANY question the user asks
    llm_response = call_llm_with_context(
        message=message,
        portfolio_value=float(portfolio_value),
        holdings_summary=holdings_summary or "none",
        prediction_accuracy=float(prediction_accuracy),
    )
    if llm_response and llm_response.strip():
        return {
            "response": llm_response.strip(),
            "suggested_followups": [
                "Analyze my portfolio",
                "What stocks should I watch?",
                "Explain SIP vs lump sum",
            ],
        }

    # Fallback: rule-based when Gemini is unavailable
    if "portfolio" in message_lower or "holdings" in message_lower:
        response = generate_portfolio_response(user, holdings, portfolio_value)
        followups = ["What stocks should I add?", "How can I reduce risk?", "Analyze my diversification"]
    elif "stock" in message_lower or "share" in message_lower or any(h.stock.symbol.lower() in message_lower for h in holdings):
        response = generate_stock_response(message, holdings)
        followups = ["Should I buy more?", "What's the price target?", "Any news on this stock?"]
    elif "risk" in message_lower or "safe" in message_lower or "protect" in message_lower:
        response = generate_risk_response(user, holdings)
        followups = ["How to diversify better?", "What are safe investments?", "Should I add bonds?"]
    elif "dividend" in message_lower or "income" in message_lower or "yield" in message_lower:
        response = generate_dividend_response()
        followups = ["Best dividend ETFs?", "Dividend vs growth stocks?", "How to build dividend income?"]
    elif "prediction" in message_lower or "forecast" in message_lower:
        response = generate_prediction_response(prediction_accuracy)
        followups = ["What's your accuracy?", "Which stocks to predict?", "How do predictions work?"]
    elif "strategy" in message_lower or "plan" in message_lower or "long term" in message_lower:
        response = generate_strategy_response(user, portfolio_value)
        followups = ["Long-term vs short-term?", "Active vs passive investing?", "How much should I invest monthly?"]
    else:
        # Try to answer company/stock name questions when Gemini is unavailable
        response = _answer_any_question_fallback(message_lower, message)
        followups = ["Analyze my portfolio", "How can I reduce risk?", "Suggest a long-term strategy"]

    return {
        "response": response,
        "suggested_followups": followups,
    }


def _answer_any_question_fallback(message_lower, original_message):
    """When Gemini is off, give a direct answer for common companies/stocks or generic guidance."""
    # Common symbols and company names (lowercase) -> richer factual answer
    company_answers = {
        "tcs": (
            "**TCS (Tata Consultancy Services)** is India’s largest IT services company and part of the Tata Group. "
            "It earns most revenue from global clients in banking, retail, and manufacturing through outsourcing, "
            "consulting, and digital transformation projects.\n\n"
            "From a retail investor view, key things to watch are: constant-currency revenue growth, operating margins, "
            "deal wins, and client concentration in US/Europe. TCS is generally considered a quality, large-cap compounder "
            "with a history of dividends and healthy balance sheet, but it is sensitive to global IT spending cycles and "
            "rupee–dollar movements. Always compare its valuation (P/E vs peers like Infosys, HCL Tech) to its growth "
            "outlook before investing. This is educational, not personalized advice."
        ),
        "reliance": (
            "**Reliance Industries** is a diversified Indian conglomerate with businesses in refining, petrochemicals, "
            "retail, and telecom (Jio). It is a major NIFTY/BSE index heavyweight and a key driver of Indian markets.\n\n"
            "For analysis, focus on: refining and petrochemical spreads, Jio subscriber growth and ARPU, retail expansion, "
            "overall debt and capex plans. The stock can be influenced by regulatory decisions, commodity cycles, and large "
            "investment projects. Consider your risk tolerance and portfolio exposure to energy and telecom before taking a "
            "position. This is educational, not personalized advice."
        ),
        "infy": (
            "**Infosys (INFY)** is a leading Indian IT services company focused on consulting, application development, "
            "and digital services for global clients. It is listed on NSE/BSE and also trades as an ADR in the US.\n\n"
            "Investors usually track: revenue growth in constant currency, deal pipeline, operating margin trends, and any "
            "management guidance. Infosys is seen as a high-quality, shareholder-friendly company, but like all IT exporters "
            "it is exposed to global recession risk and currency movements. Compare its valuation and growth prospects with "
            "peers like TCS and Wipro. This is educational, not personalized advice."
        ),
        "infosys": (
            "**Infosys (INFY)** is a leading Indian IT services company focused on consulting, application development, "
            "and digital services for global clients. It is listed on NSE/BSE and also trades as an ADR in the US.\n\n"
            "Investors usually track: revenue growth in constant currency, deal pipeline, operating margin trends, and any "
            "management guidance. Infosys is seen as a high-quality, shareholder-friendly company, but like all IT exporters "
            "it is exposed to global recession risk and currency movements. Compare its valuation and growth prospects with "
            "peers like TCS and Wipro. This is educational, not personalized advice."
        ),
        "hdfc": (
            "**HDFC Bank** is one of India’s largest private sector banks with a long track record of consistent loan growth "
            "and asset quality. It focuses on retail and SME lending, credit cards, and fee-based services.\n\n"
            "When evaluating HDFC Bank, look at net interest margin (NIM), gross and net NPA levels, CASA ratio, and loan "
            "growth versus industry. Banking stocks are sensitive to interest rate cycles and credit quality; avoid "
            "over-concentration in a single bank. This is educational, not personalized advice."
        ),
        "icici": (
            "**ICICI Bank** is a large Indian private sector bank with exposure across retail, corporate, and SME lending. "
            "It has improved asset quality in recent years and is considered one of the major private banking plays in India.\n\n"
            "Key metrics include NIM, NPA trends, provisioning, and growth in retail vs corporate book. Regulatory changes and "
            "economic cycles can affect profitability. Use it as part of a diversified financials allocation, not your only "
            "banking exposure. This is educational, not personalized advice."
        ),
        "apple": (
            "**Apple (AAPL)** is a global technology company best known for the iPhone, Mac, iPad, and services like the App "
            "Store and iCloud. It generates strong free cash flow and regularly returns capital via buybacks and dividends.\n\n"
            "Investors typically watch iPhone and services revenue growth, gross margins, product pipeline, and ecosystem lock-in. "
            "Risks include dependence on hardware cycles, regulatory scrutiny, and competition. Evaluate valuation (P/E, cash "
            "position) relative to its growth and stability. This is educational, not personalized advice."
        ),
        "aapl": (
            "**Apple (AAPL)** is a global technology company best known for the iPhone, Mac, iPad, and services like the App "
            "Store and iCloud. It generates strong free cash flow and regularly returns capital via buybacks and dividends.\n\n"
            "Investors typically watch iPhone and services revenue growth, gross margins, product pipeline, and ecosystem lock-in. "
            "Risks include dependence on hardware cycles, regulatory scrutiny, and competition. Evaluate valuation (P/E, cash "
            "position) relative to its growth and stability. This is educational, not personalized advice."
        ),
        "tesla": (
            "**Tesla (TSLA)** is an electric vehicle and clean-energy company earning revenue from EVs, batteries, and energy "
            "solutions. The stock is known for high volatility and depends heavily on growth expectations.\n\n"
            "Key factors to track: deliveries, production capacity, margins, competition from other EV makers, and regulatory "
            "support. Because TSLA trades at growth valuations, sentiment can swing sharply with news. It is usually suitable "
            "only as a smaller, higher-risk part of a diversified portfolio. This is educational, not personalized advice."
        ),
        "tsla": (
            "**Tesla (TSLA)** is an electric vehicle and clean-energy company earning revenue from EVs, batteries, and energy "
            "solutions. The stock is known for high volatility and depends heavily on growth expectations.\n\n"
            "Key factors to track: deliveries, production capacity, margins, competition from other EV makers, and regulatory "
            "support. Because TSLA trades at growth valuations, sentiment can swing sharply with news. It is usually suitable "
            "only as a smaller, higher-risk part of a diversified portfolio. This is educational, not personalized advice."
        ),
        "msft": (
            "**Microsoft (MSFT)** is a global software and cloud leader, with products like Windows, Office, Azure, and "
            "LinkedIn. It combines recurring subscription revenue with strong free cash flow and dividends.\n\n"
            "Investors focus on Azure cloud growth, Office 365 adoption, and overall margin trends. Risks include competition "
            "in cloud, regulatory scrutiny, and currency impacts. MSFT is often treated as a core large-cap holding in many "
            "portfolios. This is educational, not personalized advice."
        ),
        "microsoft": (
            "**Microsoft (MSFT)** is a global software and cloud leader, with products like Windows, Office, Azure, and "
            "LinkedIn. It combines recurring subscription revenue with strong free cash flow and dividends.\n\n"
            "Investors focus on Azure cloud growth, Office 365 adoption, and overall margin trends. Risks include competition "
            "in cloud, regulatory scrutiny, and currency impacts. MSFT is often treated as a core large-cap holding in many "
            "portfolios. This is educational, not personalized advice."
        ),
        "google": (
            "**Alphabet/Google (GOOGL)** operates core businesses in Search, YouTube, and Google Cloud, primarily monetized "
            "through advertising and subscriptions. It is a key player in digital ads and AI.\n\n"
            "When analysing GOOGL, look at ad revenue growth, YouTube engagement, cloud profitability, and spending on new "
            "bets. Main risks are regulatory pressure, competition (especially in AI), and cyclicality in ad spending. Use it "
            "as part of diversified global tech exposure. This is educational, not personalized advice."
        ),
        "googl": (
            "**Alphabet/Google (GOOGL)** operates core businesses in Search, YouTube, and Google Cloud, primarily monetized "
            "through advertising and subscriptions. It is a key player in digital ads and AI.\n\n"
            "When analysing GOOGL, look at ad revenue growth, YouTube engagement, cloud profitability, and spending on new "
            "bets. Main risks are regulatory pressure, competition (especially in AI), and cyclicality in ad spending. Use it "
            "as part of diversified global tech exposure. This is educational, not personalized advice."
        ),
    }
    for key, answer in company_answers.items():
        if key in message_lower:
            return answer
    # Default: elaborate guidance tied to the user's question
    return (
        f"Here is detailed guidance for your question about \"{original_message}\":\n\n"
        "**Diversification:** Spread your money across different assets (equity, debt, gold) and sectors. "
        "Avoid putting a large share in a single stock or theme. This reduces risk without giving up long-term return.\n\n"
        "**Time horizon and risk:** Match your investments to how long you can stay invested and how much volatility you can "
        "accept. Long-term goals (e.g. retirement) can take more equity; short-term goals need more stable options.\n\n"
        "**Systematic investing:** Use SIP or dollar-cost averaging (DCA) instead of trying to time the market. "
        "Investing a fixed amount regularly smooths out price swings and helps avoid emotional decisions.\n\n"
        "**Review and rebalance:** Check your portfolio once or twice a year and rebalance if weights have drifted. "
        "Stick to a plan rather than reacting to daily news.\n\n"
        "This is educational, not personalized financial advice."
    )


def generate_portfolio_response(user, holdings, portfolio_value):
    """Generate portfolio-specific response"""
    if not holdings:
        return """I'd be happy to analyze your portfolio, but it looks like you haven't added any holdings yet. 

**To get started:**
1. Go to the Portfolio page
2. Click "Add Stock"
3. Enter the stock symbol, shares, and purchase price

Once you have holdings, I can provide detailed analysis including:
- Risk assessment
- Diversification recommendations
- Performance insights
- Rebalancing suggestions

Would you like help with anything else in the meantime?"""
    
    # Calculate metrics
    total_gain = sum(h.gain_loss for h in holdings)
    gain_pct = (total_gain / portfolio_value) * 100 if portfolio_value > 0 else 0
    
    symbols = [h.stock.symbol for h in holdings]
    
    return f"""Based on your current portfolio analysis:

**Portfolio Overview:**
- Total Value: ${portfolio_value:,.2f}
- Total Gain/Loss: ${total_gain:,.2f} ({gain_pct:+.2f}%)
- Holdings: {', '.join(symbols)}

**Key Observations:**
Your portfolio shows {'strong' if gain_pct > 10 else 'moderate' if gain_pct > 0 else 'concerning'} performance with a {gain_pct:+.2f}% return.

**Recommendations:**
1. **Diversification**: Consider adding exposure to healthcare and international markets
2. **Risk Management**: Set stop-loss orders at -15% for individual positions
3. **Rebalancing**: Review allocations quarterly to maintain target weights

**Next Steps:**
- Monitor earnings reports for your holdings
- Consider dollar-cost averaging for new positions
- Keep 5-10% cash for opportunities

Would you like me to dive deeper into any specific aspect of your portfolio?"""


def generate_stock_response(message, holdings):
    """Generate stock-specific response"""
    # Extract stock symbol from message
    for holding in holdings:
        if holding.stock.symbol.lower() in message.lower():
            return f"""**Analysis for {holding.stock.symbol}:**

**Current Position:**
- Shares: {holding.shares}
- Avg Buy Price: ${holding.average_buy_price:.2f}
- Current Price: ${holding.stock.current_price:.2f}
- Market Value: ${holding.current_value:,.2f}
- Gain/Loss: ${holding.gain_loss:,.2f} ({holding.gain_loss_percentage:+.2f}%)

**Technical Outlook:**
The stock is currently trading {'above' if holding.stock.current_price > holding.average_buy_price else 'below'} your average buy price. 

**AI Recommendation:**
Based on recent technical analysis and market sentiment, the stock shows {'bullish' if holding.gain_loss > 0 else 'mixed'} signals. 

**Suggested Actions:**
- {'Consider taking partial profits if up >20%' if holding.gain_loss_percentage > 20 else 'Hold current position'}
- Set stop-loss at ${holding.stock.current_price * 0.85:.2f} to protect gains
- Monitor upcoming earnings and news

Would you like me to analyze another stock or provide more details on {holding.stock.symbol}?"""
    
    return """I'd be happy to analyze a specific stock for you. Please mention the stock symbol (e.g., AAPL, TSLA) in your question.

For stocks in your portfolio, I can provide:
- Current position analysis
- Gain/loss tracking
- Technical indicators
- News sentiment
- Price targets

Which stock would you like me to analyze?"""


def generate_risk_response(user, holdings):
    """Generate risk analysis response"""
    num_holdings = len(holdings)
    
    return f"""**Portfolio Risk Analysis:**

**Current Risk Profile:**
- Number of Holdings: {num_holdings}
- Risk Score: 68/100 (Moderate)
- Diversification: {'Good' if num_holdings >= 5 else 'Needs Improvement'}

**Risk Factors Identified:**
1. **Concentration Risk**: {'Low' if num_holdings >= 10 else 'Medium' if num_holdings >= 5 else 'High'} - You have {num_holdings} positions
2. **Sector Risk**: Technology-heavy portfolios are more volatile
3. **Market Risk**: General market downturns affect all holdings

**Risk Mitigation Strategies:**

1. **Diversification**
   - Aim for 10-20 different stocks
   - Spread across 5+ sectors
   - Include international exposure

2. **Position Sizing**
   - No single stock > 10% of portfolio
   - Core positions: 5-10%
   - Speculative: < 3%

3. **Stop Losses**
   - Set at -15% for growth stocks
   - Set at -10% for dividend stocks
   - Trailing stops for winners

4. **Asset Allocation**
   - Consider adding bonds (10-20%)
   - REITs for real estate exposure
   - Commodities for inflation hedge

Would you like specific recommendations for reducing your portfolio risk?"""


def generate_dividend_response():
    """Generate dividend investing response"""
    return """**Dividend Investing Guide:**

**Top Dividend Stocks to Consider:**

**Dividend Aristocrats (25+ years of increases):**
- **JNJ** - 2.9% yield, healthcare stability
- **PG** - 2.4% yield, consumer staples
- **KO** - 3.1% yield, iconic brand
- **MCD** - 2.2% yield, recession-resistant

**High Yield Options:**
- **VZ** - 6.8% yield, telecom
- **XOM** - 3.2% yield, energy recovery
- **ABBV** - 4.1% yield, pharma

**REITs for Monthly Income:**
- **O** (Realty Income) - Monthly dividends
- **VNQ** - Diversified REIT ETF

**Dividend Strategy:**
1. **Build a ladder** - Mix of yield and growth
2. **Reinvest dividends** - Compound growth
3. **Focus on sustainability** - Payout ratio < 60%
4. **Diversify sectors** - Don't chase yield

**Dividend vs Growth:**
- Dividend stocks: Better for income, less volatile
- Growth stocks: Better for capital appreciation
- Balanced approach: 60% growth, 40% dividend

Would you like specific dividend stock recommendations for your portfolio?"""


def generate_prediction_response(accuracy):
    """Generate prediction-related response"""
    return f"""**Stock Prediction System:**

**How It Works:**
Our AI analyzes multiple factors including:
- Technical indicators (RSI, MACD, Moving Averages)
- Price patterns and trends
- Volume analysis
- Market sentiment
- Historical performance

**Your Prediction Stats:**
- Your Accuracy: {accuracy}%
- AI Accuracy: 82%
- Total Predictions: Based on your history

**Prediction Tips:**
1. Look for trend confirmation
2. Consider volume spikes
3. Watch support/resistance levels
4. Factor in market sentiment
5. Don't predict on earnings days

**Best Practices:**
- Start with major stocks (AAPL, MSFT)
- Predict for next day only
- Keep a prediction journal
- Learn from incorrect predictions

**Current Market Outlook:**
The AI is currently {'bullish' if random.random() > 0.4 else 'neutral'} on the overall market based on recent technical analysis.

Ready to make a prediction? Head to the Predictions page!"""


def generate_strategy_response(user, portfolio_value):
    """Generate investment strategy response"""
    monthly_investment = portfolio_value * 0.05 if portfolio_value > 0 else 500

    # Handle anonymous or users without a profile gracefully
    if not user or not hasattr(user, "profile"):
        risk_appetite = "Moderate"
        experience_level = "Intermediate"
    else:
        risk_appetite = user.profile.risk_appetite.title()
        experience_level = user.profile.experience_level.title()

    return f"""**Investment Strategy Recommendations:**

**Based on Your Profile:**
- Risk Appetite: {risk_appetite}
- Experience: {experience_level}
- Portfolio Value: ${portfolio_value:,.2f}

**Recommended Strategy:**

**1. Dollar-Cost Averaging (DCA)**
- Invest ${monthly_investment:,.0f} monthly
- Same day each month
- Removes emotion from investing
- Smooths out market volatility

**2. Core-Satellite Approach**
- 70% Core: Index ETFs (VTI, VOO)
- 20% Satellites: Individual stocks
- 10% Speculative: Growth/opportunities

**3. Asset Allocation**
- US Stocks: 50%
- International: 20%
- Bonds: 20%
- Alternatives: 10%

**4. Rebalancing Schedule**
- Review monthly
- Rebalance quarterly
- Tax-loss harvest annually

**5. Risk Management**
- Emergency fund: 6 months expenses
- Position sizing: Max 10% per stock
- Stop losses: -15% for growth stocks

**Long-term Goals:**
- 10+ year horizon: 80% stocks, 20% bonds
- 5-10 years: 60% stocks, 40% bonds
- < 5 years: 40% stocks, 60% bonds

Would you like me to create a customized investment plan for your specific goals?"""


def generate_general_response():
    """Generic educational guidance when no specific topic is detected."""
    responses = [
        """Here are some core principles for retail investors:

- Start with a diversified portfolio across equity, debt, and cash.
- Avoid over-concentrating in one sector, theme, or single stock.
- Invest with a 3–5+ year view instead of reacting to daily noise.
- Use SIP/DCA to average into quality assets instead of timing the market.

Always treat this as educational, not personalized financial advice.""",
        """For most investors, a simple, disciplined approach works best:

- Define your goals (short term vs long term) and risk tolerance clearly.
- Use low-cost index funds/ETFs as the core of your portfolio.
- Limit speculative bets to a small portion of your capital.
- Review and rebalance your portfolio once or twice a year, not every day.

Use this as general education, not a direct recommendation.""",
        """Before taking any stock-specific decision, check three things:

- Fundamentals: revenue growth, profits, debt, and competitive position.
- Valuation: whether the price already discounts very high expectations.
- Risk: how much of your total capital is at risk if it goes wrong.

Combine this with a diversified portfolio and a long-term mindset for more stable outcomes."""
    ]

    return random.choice(responses)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history_view(request):
    """Get chat history for user"""
    session_id = request.query_params.get('session_id')
    
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            messages = ChatMessage.objects.filter(session=session)
        except ChatSession.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        # Get recent messages from all sessions
        sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[:5]
        messages = ChatMessage.objects.filter(session__in=sessions).order_by('-created_at')[:50]
    
    return Response({
        'status': 'success',
        'data': ChatMessageSerializer(messages, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggested_prompts_view(request):
    """Get suggested prompts for users"""
    prompts = SuggestedPrompt.objects.filter(is_active=True).order_by('order')[:10]
    
    return Response({
        'status': 'success',
        'data': SuggestedPromptSerializer(prompts, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendations_view(request):
    """Get AI recommendations for user"""
    recommendations = InvestmentRecommendation.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-created_at')[:10]
    
    return Response({
        'status': 'success',
        'data': InvestmentRecommendationSerializer(recommendations, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def advisor_stats_view(request):
    """Get advisor statistics"""
    user = request.user
    
    sessions = ChatSession.objects.filter(user=user)
    messages = ChatMessage.objects.filter(session__in=sessions)
    recommendations = InvestmentRecommendation.objects.filter(user=user, is_active=True)
    
    data = {
        'total_sessions': sessions.count(),
        'total_messages': messages.count(),
        'active_recommendations': recommendations.count(),
        'average_response_time': 1.5,  # Mock
        'user_satisfaction': 4.7  # Mock
    }
    
    return Response({
        'status': 'success',
        'data': data
    })
