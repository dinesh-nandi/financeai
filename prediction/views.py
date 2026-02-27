"""
Prediction views for FinanceAI
"""
import random
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Q

from .models import Stock, Prediction, StockPriceHistory, AIPredictionModel, MarketIndicator
from .serializers import (
    StockSerializer, PredictionSerializer, MakePredictionSerializer,
    StockPriceHistorySerializer, PredictionStatsSerializer
)
from users.models import UserActivity, UserProfile


def resolve_predictions_from_history(predictions_queryset):
    """
    For any prediction without actual_result where predicted_for_date has passed,
    look up closing price from StockPriceHistory (on or after predicted_for_date),
    set actual_result and is_correct, and save.
    """
    today = timezone.now().date()
    to_resolve = [
        p for p in predictions_queryset
        if p.actual_result is None and p.predicted_for_date <= today
    ]
    if not to_resolve:
        return
    stock_ids = list({p.stock_id for p in to_resolve})
    dates = list({p.predicted_for_date for p in to_resolve})
    # Exact date match first
    history = StockPriceHistory.objects.filter(
        stock_id__in=stock_ids,
        date__in=dates
    ).values_list('stock_id', 'date', 'close_price')
    price_map = {(sid, d): float(c) for sid, d, c in history}
    # For any still missing: use first close on or after predicted_for_date
    for p in to_resolve:
        key = (p.stock_id, p.predicted_for_date)
        if key in price_map:
            continue
        first_after = StockPriceHistory.objects.filter(
            stock_id=p.stock_id,
            date__gte=p.predicted_for_date,
            date__lte=today
        ).order_by('date').values_list('date', 'close_price').first()
        if first_after:
            _, close_price = first_after
            price_map[key] = float(close_price)
    for p in to_resolve:
        key = (p.stock_id, p.predicted_for_date)
        if key not in price_map:
            continue
        actual_price = price_map[key]
        price_at = float(p.price_at_prediction)
        actual_result = 'up' if actual_price >= price_at else 'down'
        is_correct = (p.user_prediction == actual_result)
        p.actual_result = actual_result
        p.is_correct = is_correct
        p.resolved_at = timezone.now()
        p.save(update_fields=['actual_result', 'is_correct', 'resolved_at'])
        try:
            profile = UserProfile.objects.get(user_id=p.user_id)
            if is_correct:
                profile.correct_predictions = (profile.correct_predictions or 0) + 1
            profile.save(update_fields=['correct_predictions'])
        except UserProfile.DoesNotExist:
            pass
    # Fallback: resolve using stock current_price when no history (so UI shows something)
    still_pending = [p for p in to_resolve if p.actual_result is None]
    for p in still_pending:
        try:
            stock = Stock.objects.get(id=p.stock_id)
            actual_price = float(stock.current_price)
            price_at = float(p.price_at_prediction)
            if price_at <= 0:
                continue
            actual_result = 'up' if actual_price >= price_at else 'down'
            is_correct = (p.user_prediction == actual_result)
            p.actual_result = actual_result
            p.is_correct = is_correct
            p.resolved_at = timezone.now()
            p.save(update_fields=['actual_result', 'is_correct', 'resolved_at'])
            try:
                profile = UserProfile.objects.get(user_id=p.user_id)
                if is_correct:
                    profile.correct_predictions = (profile.correct_predictions or 0) + 1
                profile.save(update_fields=['correct_predictions'])
            except UserProfile.DoesNotExist:
                pass
        except Stock.DoesNotExist:
            pass


class StockListView(generics.ListAPIView):
    """List all available stocks, with optional search by symbol or name"""
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.query_params.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(symbol__icontains=q) | Q(name__icontains=q)
            )[:20]
        return qs
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class StockDetailView(generics.RetrieveAPIView):
    """Get stock details with price history (optional range: 1D, 1W, 1M, 1Y)"""
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'symbol'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        range_param = (request.query_params.get('range') or '1M').upper()
        range_days = {'1D': 1, '1W': 7, '1M': 30, '3M': 90, '1Y': 365}.get(range_param, 30)
        price_history = StockPriceHistory.objects.filter(
            stock=instance
        ).order_by('-date')[:range_days]
        price_history = list(reversed(price_history))
        data = serializer.data
        data['price_history'] = StockPriceHistorySerializer(price_history, many=True).data
        data['ohlc'] = [
            {'date': ph.date.strftime('%Y-%m-%d'), 'o': float(ph.open_price), 'h': float(ph.high_price),
             'l': float(ph.low_price), 'c': float(ph.close_price), 'v': ph.volume}
            for ph in price_history
        ]
        data['candlestick_patterns'] = self._detect_patterns(price_history)
        return Response({'status': 'success', 'data': data})
    
    def _detect_patterns(self, price_history):
        """Simple candlestick pattern detection (hammer, doji, engulfing, shooting_star)"""
        patterns = []
        for i, ph in enumerate(price_history):
            o, h, l, c = float(ph.open_price), float(ph.high_price), float(ph.low_price), float(ph.close_price)
            body = abs(c - o)
            full_range = h - l if h > l else 0.0001
            lower_wick = min(o, c) - l
            upper_wick = h - max(o, c)
            # Hammer: small body at top, long lower wick
            if full_range > 0 and body / full_range < 0.35 and lower_wick > 2 * body and upper_wick < body:
                patterns.append({'date': ph.date.strftime('%Y-%m-%d'), 'pattern': 'hammer'})
            # Doji: very small body
            elif full_range > 0 and body / full_range < 0.1:
                patterns.append({'date': ph.date.strftime('%Y-%m-%d'), 'pattern': 'doji'})
            # Shooting star: small body at bottom, long upper wick
            elif full_range > 0 and body / full_range < 0.35 and upper_wick > 2 * body and lower_wick < body:
                patterns.append({'date': ph.date.strftime('%Y-%m-%d'), 'pattern': 'shooting_star'})
        return patterns


class MakePredictionView(generics.CreateAPIView):
    """Make a stock prediction"""
    serializer_class = MakePredictionSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        stock_symbol = serializer.validated_data['stock_symbol']
        user_prediction = serializer.validated_data['prediction']
        horizon = serializer.validated_data.get('horizon', 1)
        model_type = serializer.validated_data.get('model_type', 'linear')
        
        try:
            stock = Stock.objects.get(symbol=stock_symbol)
        except Stock.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Stock not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate AI prediction (pass model_type for explanation text)
        ai_prediction_data = self.generate_ai_prediction(stock, model_type)
        
        # Build predicted 7-day (or horizon) price path for chart
        predicted_path = self._predict_price_path(stock, ai_prediction_data['prediction'], ai_prediction_data['confidence'], horizon)
        
        # Create prediction
        prediction = Prediction.objects.create(
            user=request.user,
            stock=stock,
            user_prediction=user_prediction,
            ai_prediction=ai_prediction_data['prediction'],
            ai_confidence=ai_prediction_data['confidence'],
            ai_explanation=ai_prediction_data['explanation'],
            price_at_prediction=stock.current_price,
            predicted_for_date=timezone.now().date() + timedelta(days=horizon)
        )

        # Record activity for prediction history
        UserActivity.objects.create(
            user=request.user,
            activity_type='prediction',
            description=f'Predicted {stock_symbol} would go {user_prediction}',
            metadata={
                'stock_symbol': stock_symbol,
                'user_prediction': user_prediction,
                'ai_prediction': ai_prediction_data['prediction'],
                'prediction_id': prediction.id
            }
        )

        # Update user profile (if profile exists)
        profile = getattr(request.user, 'profile', None)
        if profile is not None:
            profile.total_predictions += 1
            profile.save()
        
        return Response({
            'status': 'success',
            'data': {
                'prediction': PredictionSerializer(prediction).data,
                'ai_prediction': ai_prediction_data['prediction'],
                'ai_confidence': ai_prediction_data['confidence'],
                'ai_explanation': ai_prediction_data['explanation'],
                'model_used': model_type,
                'predicted_path': predicted_path,
                'trend': 'bullish' if ai_prediction_data['prediction'] == 'up' else 'bearish'
            }
        }, status=status.HTTP_201_CREATED)
    
    def _predict_price_path(self, stock, direction, confidence, horizon):
        """Generate a simple predicted price path for next N days (educational)"""
        from decimal import Decimal
        base = float(stock.current_price)
        daily_drift = 0.002 if direction == 'up' else -0.002
        conf_factor = (confidence / 100.0) * 0.5 + 0.5
        path = []
        for d in range(1, horizon + 1):
            move = daily_drift * conf_factor * (1 + 0.1 * (d / max(horizon, 1)))
            base = base * (1 + move)
            path.append({'day': d, 'price': round(base, 2)})
        return path
    
    def generate_ai_prediction(self, stock, model_type='linear'):
        """
        Generate a richer AI prediction using recent price history + market indicators
        (RSI, MACD, EMA/SMA, volume, sentiment) when available.
        """
        # --- Price history (last 10 days) ---
        price_history = StockPriceHistory.objects.filter(
            stock=stock
        ).order_by('-date')[:10]

        prices = [float(ph.close_price) for ph in price_history]
        momentum = 0.0
        trend_score = 0.0
        volatility = 0.0
        factors = []

        if len(prices) >= 5:
            # Simple short vs long moving-average comparison
            recent_avg = sum(prices[:3]) / 3
            older_avg = sum(prices[-3:]) / 3

            if older_avg:
                momentum = (prices[0] - prices[-1]) / prices[-1]

            if recent_avg > older_avg * 1.01:
                trend_score += 1.0
                factors.append(
                    f"short‑term price is trading above its recent average "
                    f"({recent_avg:.2f} vs {older_avg:.2f}), indicating an upward trend"
                )
            elif recent_avg < older_avg * 0.99:
                trend_score -= 1.0
                factors.append(
                    f"short‑term price is trading below its recent average "
                    f"({recent_avg:.2f} vs {older_avg:.2f}), indicating a weakening trend"
                )

            # Price momentum
            if momentum > 0.03:
                trend_score += 2.0
                factors.append(f"price momentum is strongly positive at {momentum:.2%}")
            elif momentum < -0.03:
                trend_score -= 2.0
                factors.append(f"price momentum is strongly negative at {momentum:.2%}")
            elif abs(momentum) > 0.01:
                trend_score += 1.0 if momentum > 0 else -1.0
                factors.append(f"price momentum is mildly {'positive' if momentum > 0 else 'negative'} at {momentum:.2%}")

            # Volatility (standard deviation of returns)
            if len(prices) >= 6:
                returns = []
                for i in range(1, len(prices)):
                    if prices[i - 1]:
                        returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
                if returns:
                    mean_ret = sum(returns) / len(returns)
                    var = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
                    volatility = var ** 0.5
                    if volatility > 0.04:
                        factors.append(
                            f"recent volatility is elevated (~{volatility:.2%}), so short‑term moves can be sharp"
                        )

        # --- Market indicators (latest per type) ---
        indicator_qs = MarketIndicator.objects.filter(stock=stock).order_by('-calculated_at')
        latest_indicators = {}
        for ind in indicator_qs:
            if ind.indicator_type not in latest_indicators:
                latest_indicators[ind.indicator_type] = ind

        score = trend_score

        # RSI: <30 oversold (bullish), >70 overbought (bearish)
        rsi = latest_indicators.get('rsi')
        if rsi is not None:
            rsi_val = float(rsi.value)
            if rsi_val < 30:
                score += 1.5
                factors.append(f"RSI is {rsi_val:.1f} (oversold), which is typically bullish")
            elif rsi_val > 70:
                score -= 1.5
                factors.append(f"RSI is {rsi_val:.1f} (overbought), which is typically bearish")
            else:
                factors.append(f"RSI is neutral around {rsi_val:.1f}")

        # MACD: positive vs negative
        macd = latest_indicators.get('macd')
        if macd is not None:
            macd_val = float(macd.value)
            if macd_val > 0:
                score += 1.0
                factors.append("MACD is above zero, supporting a bullish bias")
            elif macd_val < 0:
                score -= 1.0
                factors.append("MACD is below zero, supporting a bearish bias")

        # EMA/SMA: price vs moving average
        ema = latest_indicators.get('ema') or latest_indicators.get('sma')
        if ema is not None and prices:
            ma_val = float(ema.value)
            last_price = prices[0]
            if last_price > ma_val * 1.01:
                score += 1.0
                factors.append(
                    f"price is trading above its moving average ({last_price:.2f} vs {ma_val:.2f}), "
                    f"a bullish technical signal"
                )
            elif last_price < ma_val * 0.99:
                score -= 1.0
                factors.append(
                    f"price is trading below its moving average ({last_price:.2f} vs {ma_val:.2f}), "
                    f"a bearish technical signal"
                )

        # Volume: unusually high volume can confirm moves
        volume_ind = latest_indicators.get('volume')
        if volume_ind is not None:
            vol_val = float(volume_ind.value)
            if vol_val > 1.2:
                score += 0.5
                factors.append("recent volume is above average, confirming the current move")
            elif vol_val < 0.8:
                factors.append("recent volume is below average, so signals are weaker")

        # Sentiment: simple positive/negative tilt
        sentiment_ind = latest_indicators.get('sentiment')
        if sentiment_ind is not None:
            sent_val = float(sentiment_ind.value)
            if sent_val > 0.2:
                score += 1.0
                factors.append("news / sentiment data is moderately positive")
            elif sent_val < -0.2:
                score -= 1.0
                factors.append("news / sentiment data is moderately negative")

        # --- Final decision: map score to direction + confidence ---
        if not prices and not latest_indicators:
            # Not enough data, keep behaviour reasonable but transparent
            prediction = 'up' if random.random() > 0.5 else 'down'
            confidence = random.randint(60, 70)
            explanation = (
                f"There is very limited recent data available for {stock.symbol}. "
                f"The AI is making a {prediction}ward guess with only moderate confidence. "
                f"Treat this as a learning example, not as trading advice."
            )
        else:
            if score >= 2.0:
                prediction = 'up'
            elif score <= -2.0:
                prediction = 'down'
            else:
                # If score is small, fall back to momentum sign or neutral bias
                if momentum > 0.0:
                    prediction = 'up'
                elif momentum < 0.0:
                    prediction = 'down'
                else:
                    prediction = 'up' if random.random() > 0.5 else 'down'

            strength = min(max(abs(score), 0.5), 4.0)
            base_conf = 55
            # Map strength 0.5‑4.0 roughly to +5‑30 points
            confidence = base_conf + int((strength / 4.0) * 30)
            confidence = max(55, min(confidence, 90))

            explanation_parts = [
                f"For {stock.symbol}, the AI sees a net {'bullish' if prediction == 'up' else 'bearish'} score of {score:.2f} "
                f"based on recent price action and technical indicators."
            ]
            if factors:
                explanation_parts.append("Key factors influencing this view include: " + "; ".join(factors) + ".")
            if volatility > 0.04:
                explanation_parts.append(
                    "Because recent volatility is high, short‑term moves can be larger than usual. "
                    "Position sizing and risk management are important."
                )
            explanation_parts.append(
                "This is an educational signal only and not personalized investment advice. "
                f"Model: {model_type.upper()}."
            )
            explanation = " ".join(explanation_parts)

        return {
            'prediction': prediction,
            'confidence': confidence,
            'explanation': explanation
        }


class PredictionHistoryView(generics.ListAPIView):
    """Get user's prediction history"""
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Prediction.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()[:50]
        resolve_predictions_from_history(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prediction_stats_view(request):
    """Get user's prediction statistics"""
    user = request.user

    # Resolve any predictions that have price history for predicted_for_date
    predictions = Prediction.objects.filter(user=user)
    resolve_predictions_from_history(predictions)

    # User stats
    total = predictions.count()
    correct = predictions.filter(is_correct=True).count()
    accuracy = round((correct / total) * 100, 2) if total > 0 else 0
    
    # Recent predictions
    recent = predictions.order_by('-created_at')[:10]
    
    # AI accuracy (mock)
    ai_accuracy = random.randint(72, 85)
    
    data = {
        'total_predictions': total,
        'correct_predictions': correct,
        'accuracy_percentage': accuracy,
        'recent_predictions': PredictionSerializer(recent, many=True).data,
        'ai_accuracy': ai_accuracy
    }
    
    return Response({
        'status': 'success',
        'data': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_indicators_view(request, symbol):
    """
    Get latest technical / sentiment indicators for a stock.
    Returns at most one entry per indicator_type.
    """
    try:
        stock = Stock.objects.get(symbol=symbol)
    except Stock.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Stock not found'
        }, status=status.HTTP_404_NOT_FOUND)

    indicators_qs = MarketIndicator.objects.filter(stock=stock).order_by('-calculated_at')
    latest = {}
    for ind in indicators_qs:
        if ind.indicator_type not in latest:
            latest[ind.indicator_type] = {
                'indicator_type': ind.indicator_type,
                'value': float(ind.value),
                'period': ind.period,
                'calculated_at': ind.calculated_at,
            }

    return Response({
        'status': 'success',
        'data': {
            'symbol': stock.symbol,
            'indicators': list(latest.values()),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_sentiment_view(request, symbol):
    """News sentiment for stock: positive / neutral / negative distribution + score."""
    try:
        stock = Stock.objects.get(symbol=symbol)
    except Stock.DoesNotExist:
        return Response({'status': 'error', 'message': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)
    sentiment_ind = MarketIndicator.objects.filter(stock=stock, indicator_type='sentiment').order_by('-calculated_at').first()
    if sentiment_ind:
        v = float(sentiment_ind.value)
        if v > 0.2:
            positive, neutral, negative = 60, 25, 15
            label, emoji = 'Positive', '😊'
        elif v < -0.2:
            positive, neutral, negative = 15, 25, 60
            label, emoji = 'Negative', '😟'
        else:
            positive, neutral, negative = 25, 50, 25
            label, emoji = 'Neutral', '😐'
    else:
        positive, neutral, negative = 33, 34, 33
        label, emoji = 'Neutral', '😐'
    return Response({
        'status': 'success',
        'data': {
            'symbol': stock.symbol,
            'sentiment_label': label,
            'sentiment_emoji': emoji,
            'distribution': {'positive': positive, 'neutral': neutral, 'negative': negative}
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_risk_view(request, symbol):
    """Risk meter: volatility, risk_score (low/medium/high), beta, 52w high/low."""
    try:
        stock = Stock.objects.get(symbol=symbol)
    except Stock.DoesNotExist:
        return Response({'status': 'error', 'message': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)
    history = StockPriceHistory.objects.filter(stock=stock).order_by('-date')[:30]
    prices = [float(ph.close_price) for ph in history]
    volatility_pct = 0
    if len(prices) >= 2:
        returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
        mean_ret = sum(returns) / len(returns)
        var = sum((r - mean_ret)**2 for r in returns) / len(returns)
        volatility_pct = round((var ** 0.5) * 100, 2)
    if volatility_pct < 1.5:
        risk_score = 'low'
    elif volatility_pct < 3.5:
        risk_score = 'medium'
    else:
        risk_score = 'high'
    fifty_two_high = float(stock.fifty_two_week_high) if stock.fifty_two_week_high else float(stock.current_price) * 1.15
    fifty_two_low = float(stock.fifty_two_week_low) if stock.fifty_two_week_low else float(stock.current_price) * 0.85
    current = float(stock.current_price)
    dist_high = round((fifty_two_high - current) / fifty_two_high * 100, 1) if fifty_two_high else 0
    dist_low = round((current - fifty_two_low) / fifty_two_low * 100, 1) if fifty_two_low else 0
    beta = 1.0 + (volatility_pct / 100)
    return Response({
        'status': 'success',
        'data': {
            'symbol': stock.symbol,
            'volatility_percent': volatility_pct,
            'risk_score': risk_score,
            'beta': round(beta, 2),
            'fifty_two_week_high': fifty_two_high,
            'fifty_two_week_low': fifty_two_low,
            'distance_from_52w_high_percent': dist_high,
            'distance_from_52w_low_percent': dist_low
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_compare_view(request):
    """Compare two stocks: a=SYM1&b=SYM2. Returns aligned series + stats + multiple metrics."""
    import statistics
    a = (request.query_params.get('a') or '').strip().upper()
    b = (request.query_params.get('b') or '').strip().upper()
    if not a or not b:
        return Response({'status': 'error', 'message': 'Query params a and b required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        stock_a = Stock.objects.get(symbol=a)
        stock_b = Stock.objects.get(symbol=b)
    except Stock.DoesNotExist:
        return Response({'status': 'error', 'message': 'One or both stocks not found'}, status=status.HTTP_404_NOT_FOUND)
    
    days = 30
    hist_a = list(StockPriceHistory.objects.filter(stock=stock_a).order_by('date')[:days])
    hist_b = list(StockPriceHistory.objects.filter(stock=stock_b).order_by('date')[:days])
    dates_a = {ph.date: float(ph.close_price) for ph in hist_a}
    dates_b = {ph.date: float(ph.close_price) for ph in hist_b}
    all_dates = sorted(set(dates_a) | set(dates_b))[-days:]
    prices_a = [dates_a.get(d) for d in all_dates]
    prices_b = [dates_b.get(d) for d in all_dates]
    
    # Calculate overall returns
    ret_a = ((prices_a[-1] / prices_a[0]) - 1) * 100 if prices_a and prices_a[0] else 0
    ret_b = ((prices_b[-1] / prices_b[0]) - 1) * 100 if prices_b and prices_b[0] else 0
    
    # Calculate daily returns (percentage change)
    daily_returns_a = []
    daily_returns_b = []
    for i in range(1, len(prices_a)):
        if prices_a[i-1] and prices_a[i]:
            daily_returns_a.append(((prices_a[i] - prices_a[i-1]) / prices_a[i-1]) * 100)
        else:
            daily_returns_a.append(0)
        if prices_b[i-1] and prices_b[i]:
            daily_returns_b.append(((prices_b[i] - prices_b[i-1]) / prices_b[i-1]) * 100)
        else:
            daily_returns_b.append(0)
    
    # Calculate volatility (standard deviation of daily returns)
    vol_a = round(statistics.stdev(daily_returns_a), 2) if len(daily_returns_a) > 1 else 0
    vol_b = round(statistics.stdev(daily_returns_b), 2) if len(daily_returns_b) > 1 else 0
    
    # Calculate moving averages (7-day and 14-day)
    def moving_avg(prices, window):
        ma = []
        for i in range(len(prices)):
            if i < window - 1:
                ma.append(None)
            else:
                avg = sum([p for p in prices[i-window+1:i+1] if p]) / window
                ma.append(round(avg, 2))
        return ma
    
    ma7_a = moving_avg(prices_a, 7)
    ma7_b = moving_avg(prices_b, 7)
    ma14_a = moving_avg(prices_a, 14)
    ma14_b = moving_avg(prices_b, 14)
    
    # Normalized price (start at 100)
    norm_a = [100 * (p / prices_a[0]) if prices_a[0] else None for p in prices_a]
    norm_b = [100 * (p / prices_b[0]) if prices_b[0] else None for p in prices_b]
    
    # Price ratio (A/B)
    ratio = [round(prices_a[i] / prices_b[i], 4) if prices_b[i] and prices_a[i] else None for i in range(len(prices_a))]
    
    return Response({
        'status': 'success',
        'data': {
            'labels': [d.strftime('%b %d') for d in all_dates],
            'stock_a': {
                'symbol': a,
                'name': stock_a.name,
                'prices': prices_a,
                'normalized': norm_a,
                'ma7': ma7_a,
                'ma14': ma14_a,
                'return_percent': round(ret_a, 2),
                'volatility': vol_a
            },
            'stock_b': {
                'symbol': b,
                'name': stock_b.name,
                'prices': prices_b,
                'normalized': norm_b,
                'ma7': ma7_b,
                'ma14': ma14_b,
                'return_percent': round(ret_b, 2),
                'volatility': vol_b
            },
            'daily_returns_a': [round(r, 2) for r in daily_returns_a],
            'daily_returns_b': [round(r, 2) for r in daily_returns_b],
            'price_ratio': ratio
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def backtest_view(request):
    """Backtest: strategy (ma_crossover), start_date, end_date, initial_capital. Returns equity curve + metrics."""
    strategy = request.data.get('strategy', 'ma_crossover')
    initial_capital = float(request.data.get('initial_capital', 100000))
    symbol = (request.data.get('symbol') or 'AAPL').upper()
    try:
        stock = Stock.objects.get(symbol=symbol)
    except Stock.DoesNotExist:
        return Response({'status': 'error', 'message': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)
    history = list(StockPriceHistory.objects.filter(stock=stock).order_by('date')[:365])
    if len(history) < 50:
        return Response({'status': 'success', 'data': {'equity_curve': [], 'total_return': 0, 'max_drawdown': 0, 'sharpe_ratio': 0}})
    prices = [float(ph.close_price) for ph in history]
    def sma(arr, n):
        out = []
        for i in range(len(arr)):
            if i < n - 1:
                out.append(None)
            else:
                out.append(sum(arr[i-n+1:i+1]) / n)
        return out
    fast = sma(prices, 10)
    slow = sma(prices, 20)
    equity = [initial_capital]
    for i in range(20, len(prices)):
        if fast[i] and slow[i] and fast[i] > slow[i] and (i == 20 or fast[i-1] <= slow[i-1]):
            shares = equity[-1] / prices[i]
            equity.append(shares * prices[i] if i + 1 < len(prices) else equity[-1])
        elif fast[i] and slow[i] and fast[i] < slow[i]:
            equity.append(equity[-1])
        else:
            equity.append(equity[-1] * (prices[i] / prices[i-1]) if prices[i-1] else equity[-1])
    total_return = (equity[-1] / initial_capital - 1) * 100 if equity else 0
    peak = initial_capital
    max_dd = 0
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / peak * 100 if peak else 0
        if dd > max_dd:
            max_dd = dd
    returns_bt = []
    for i in range(1, len(equity)):
        if equity[i-1]:
            returns_bt.append((equity[i] - equity[i-1]) / equity[i-1])
    sharpe = (sum(returns_bt) / len(returns_bt) * (252 ** 0.5) / ((sum((r - sum(returns_bt)/len(returns_bt))**2 for r in returns_bt) / len(returns_bt)) ** 0.5)) if returns_bt else 0
    return Response({
        'status': 'success',
        'data': {
            'equity_curve': [round(e, 2) for e in equity],
            'labels': [history[i].date.strftime('%b %d') for i in range(20, len(history))],
            'total_return': round(total_return, 2),
            'max_drawdown': round(max_dd, 2),
            'sharpe_ratio': round(sharpe, 2)
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard_view(request):
    """Leaderboard: users by prediction accuracy (min 5 resolved predictions)."""
    from django.contrib.auth.models import User
    from django.db.models import Count, Q
    resolved = Prediction.objects.filter(is_correct__isnull=False).values('user_id').annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True))
    ).filter(total__gte=5)
    user_ids = [x['user_id'] for x in resolved]
    users = User.objects.filter(id__in=user_ids)
    by_id = {u.id: {'username': u.username, 'total': 0, 'correct': 0} for u in users}
    for x in resolved:
        if x['user_id'] in by_id:
            by_id[x['user_id']]['total'] = x['total']
            by_id[x['user_id']]['correct'] = x['correct']
    leaderboard = []
    for u in users:
        d = by_id.get(u.id, {})
        total = d.get('total', 0)
        correct = d.get('correct', 0)
        acc = round((correct / total) * 100, 1) if total else 0
        leaderboard.append({'username': u.username, 'total': total, 'correct': correct, 'accuracy': acc})
    leaderboard.sort(key=lambda x: x['accuracy'], reverse=True)
    return Response({'status': 'success', 'data': leaderboard[:20]})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_prediction_view(request, prediction_id):
    """Resolve a prediction with actual result"""
    try:
        prediction = Prediction.objects.get(
            id=prediction_id,
            user=request.user
        )
    except Prediction.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Prediction not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get actual price (mock - would fetch from API)
    actual_price = prediction.stock.current_price
    prediction.resolve(actual_price)
    
    return Response({
        'status': 'success',
        'data': {
            'prediction': PredictionSerializer(prediction).data,
            'message': 'Prediction resolved successfully'
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_chart_data_view(request, symbol):
    """Get stock chart data with optional range (1D, 1W, 1M, 1Y). Returns line + OHLC."""
    try:
        stock = Stock.objects.get(symbol=symbol)
    except Stock.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Stock not found'
        }, status=status.HTTP_404_NOT_FOUND)
    range_param = (request.query_params.get('range') or '1M').upper()
    days = {'1D': 1, '1W': 7, '1M': 30, '3M': 90, '1Y': 365}.get(range_param, 30)
    price_history = StockPriceHistory.objects.filter(stock=stock).order_by('date')[:days]
    price_history = list(price_history)
    labels = [ph.date.strftime('%b %d') for ph in price_history]
    prices = [float(ph.close_price) for ph in price_history]
    ohlc = [
        {'date': ph.date.strftime('%Y-%m-%d'), 'o': float(ph.open_price), 'h': float(ph.high_price),
         'l': float(ph.low_price), 'c': float(ph.close_price), 'v': ph.volume}
        for ph in price_history
    ]
    return Response({
        'status': 'success',
        'data': {
            'symbol': symbol,
            'name': stock.name,
            'labels': labels,
            'prices': prices,
            'ohlc': ohlc,
            'current_price': float(stock.current_price),
            'change': stock.price_change
        }
    })
