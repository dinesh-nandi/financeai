#!/usr/bin/env python
"""
Setup script for FinanceAI Django Backend
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_ai.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from prediction.models import Stock, StockPriceHistory
from learning.models import Topic, QuizQuestion
from advisor.models import SuggestedPrompt


def create_sample_stocks():
    """Create sample stocks"""
    stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology', 'current_price': 182.50, 'previous_close': 180.25},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'sector': 'Technology', 'current_price': 215.30, 'previous_close': 217.10},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology', 'current_price': 141.20, 'previous_close': 139.85},
        {'symbol': 'MSFT', 'name': 'Microsoft Corp.', 'sector': 'Technology', 'current_price': 312.45, 'previous_close': 307.80},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': 'Consumer', 'current_price': 145.80, 'previous_close': 146.45},
        {'symbol': 'INFY', 'name': 'Infosys Ltd.', 'sector': 'Technology', 'current_price': 19.85, 'previous_close': 19.72},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corp.', 'sector': 'Technology', 'current_price': 485.10, 'previous_close': 478.20},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'sector': 'Technology', 'current_price': 325.45, 'previous_close': 320.15},
    ]
    
    for stock_data in stocks:
        Stock.objects.get_or_create(
            symbol=stock_data['symbol'],
            defaults=stock_data
        )
    
    print(f"[OK] Created {len(stocks)} sample stocks")
    create_sample_price_history()


def create_sample_price_history():
    """Add ~30 days of sample OHLC history for each stock so the prediction chart has data."""
    from datetime import date
    today = timezone.now().date()
    created = 0
    for stock in Stock.objects.all():
        # Skip if we already have recent history
        if StockPriceHistory.objects.filter(stock=stock).exists():
            continue
        base = float(stock.current_price)
        prev = float(stock.previous_close)
        for i in range(30, -1, -1):
            d = today - timedelta(days=i)
            # Simple random walk: small daily change
            import random
            random.seed(hash(stock.symbol + d.isoformat()) % (2**32))
            change = (random.random() - 0.48) * 0.02
            o = base
            base = base * (1 + change)
            c = base
            h = max(o, c) * (1 + random.random() * 0.01)
            l = min(o, c) * (1 - random.random() * 0.01)
            vol = random.randint(5_000_000, 50_000_000)
            StockPriceHistory.objects.get_or_create(
                stock=stock,
                date=d,
                defaults={
                    'open_price': Decimal(str(round(o, 2))),
                    'high_price': Decimal(str(round(h, 2))),
                    'low_price': Decimal(str(round(l, 2))),
                    'close_price': Decimal(str(round(c, 2))),
                    'volume': vol,
                }
            )
            created += 1
    if created:
        print(f"[OK] Created {created} sample price history records")


def create_sample_topics():
    """Create sample learning topics"""
    topics = [
        {
            'title': 'Introduction to Stocks',
            'slug': 'intro-to-stocks',
            'category': 'basics',
            'description': 'Learn the fundamentals of stocks and how they work',
            'content': """
<h4>What is a Stock?</h4>
<p>A stock, also known as equity, is a security that represents the ownership of a fraction of a corporation.</p>
<h4>How Do Stocks Work?</h4>
<p>When you buy a company's stock, you're purchasing a small piece of that company, called a share.</p>
<h4>Key Terms</h4>
<ul>
    <li><strong>Market Cap:</strong> The total value of a company's shares</li>
    <li><strong>Dividend:</strong> A portion of profits paid to shareholders</li>
    <li><strong>IPO:</strong> Initial Public Offering</li>
</ul>
            """,
            'icon': '📚',
            'order': 1,
            'estimated_duration': 15
        },
        {
            'title': 'Understanding Market Cap',
            'slug': 'understanding-market-cap',
            'category': 'basics',
            'description': 'Learn about market capitalization and its importance',
            'content': '<h4>Market Capitalization</h4><p>Market cap is calculated by multiplying the stock price by the number of outstanding shares.</p>',
            'icon': '📊',
            'order': 2,
            'estimated_duration': 20
        },
        {
            'title': 'Reading Candlestick Charts',
            'slug': 'candlestick-charts',
            'category': 'technical',
            'description': 'Master the art of reading candlestick charts',
            'content': '<h4>Candlestick Basics</h4><p>Candlesticks show the open, high, low, and close prices for a given period.</p>',
            'icon': '📈',
            'order': 1,
            'estimated_duration': 30
        },
        {
            'title': 'Diversification Strategy',
            'slug': 'diversification-strategy',
            'category': 'portfolio',
            'description': 'Learn how to diversify your portfolio effectively',
            'content': '<h4>What is Diversification?</h4><p>Diversification is a risk management strategy that mixes a variety of investments.</p>',
            'icon': '💰',
            'order': 1,
            'estimated_duration': 35
        },
    ]
    
    for topic_data in topics:
        Topic.objects.get_or_create(
            slug=topic_data['slug'],
            defaults=topic_data
        )
    
    print(f"[OK] Created {len(topics)} sample topics")


def create_sample_quiz_questions():
    """Create sample quiz questions"""
    try:
        topic = Topic.objects.get(slug='intro-to-stocks')
        
        questions = [
            {
                'topic': topic,
                'question': 'What is a stock?',
                'options': [
                    'A type of bond issued by companies',
                    'A share of ownership in a company',
                    'A government-issued security',
                    'A type of bank account'
                ],
                'correct_answer': 1,
                'explanation': 'A stock represents ownership in a company.',
                'order': 1
            },
            {
                'topic': topic,
                'question': 'What does IPO stand for?',
                'options': [
                    'International Profit Organization',
                    'Initial Public Offering',
                    'Internal Price Operation',
                    'Investment Portfolio Option'
                ],
                'correct_answer': 1,
                'explanation': 'IPO stands for Initial Public Offering.',
                'order': 2
            },
        ]
        
        for q_data in questions:
            QuizQuestion.objects.get_or_create(
                topic=q_data['topic'],
                question=q_data['question'],
                defaults=q_data
            )
        
        print(f"[OK] Created {len(questions)} sample quiz questions")
    except Topic.DoesNotExist:
        print("⚠ Topic not found, skipping quiz questions")


def create_suggested_prompts():
    """Create suggested prompts for AI advisor"""
    prompts = [
        {'prompt': 'Should I invest in tech stocks right now?', 'category': 'stock', 'icon': '💬'},
        {'prompt': 'Analyze my portfolio risk', 'category': 'portfolio', 'icon': '💬'},
        {'prompt': 'What are the best dividend stocks?', 'category': 'stock', 'icon': '💬'},
        {'prompt': 'How do I diversify my portfolio?', 'category': 'portfolio', 'icon': '💬'},
        {'prompt': 'Explain dollar-cost averaging', 'category': 'learning', 'icon': '💬'},
        {'prompt': 'Generate a portfolio report', 'category': 'portfolio', 'icon': '📊'},
        {'prompt': 'What stocks should I watch this week?', 'category': 'stock', 'icon': '👀'},
        {'prompt': 'Give me market outlook for next month', 'category': 'strategy', 'icon': '🔮'},
        {'prompt': 'Suggest a low-risk investment strategy', 'category': 'strategy', 'icon': '🛡️'},
    ]
    
    for prompt_data in prompts:
        SuggestedPrompt.objects.get_or_create(
            prompt=prompt_data['prompt'],
            defaults=prompt_data
        )
    
    print(f"[OK] Created {len(prompts)} suggested prompts")


def main():
    """Main setup function"""
    print("=" * 50)
    print("FinanceAI Django Backend Setup")
    print("=" * 50)
    
    print("\nCreating sample data...\n")
    
    create_sample_stocks()
    create_sample_topics()
    create_sample_quiz_questions()
    create_suggested_prompts()
    
    print("\n" + "=" * 50)
    print("Setup complete! You can now run the server:")
    print("  python manage.py runserver")
    print("=" * 50)


if __name__ == '__main__':
    main()
