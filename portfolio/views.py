"""
Portfolio views for FinanceAI
"""
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum

from .models import Portfolio, PortfolioTransaction, PortfolioAnalytics, PortfolioHistory
from .serializers import (
    PortfolioSerializer, AddPortfolioSerializer, PortfolioTransactionSerializer,
    PortfolioAnalyticsSerializer, PortfolioSummarySerializer,
    PortfolioHistorySerializer, AllocationDataSerializer
)


class PortfolioListView(generics.ListAPIView):
    """List user's portfolio holdings"""
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class AddPortfolioView(generics.CreateAPIView):
    """Add stock to portfolio"""
    serializer_class = AddPortfolioSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from prediction.models import Stock
        
        stock_symbol = serializer.validated_data['stock_symbol'].upper()
        shares = serializer.validated_data['shares']
        purchase_price = serializer.validated_data['purchase_price']
        
        # Get or create stock
        try:
            stock = Stock.objects.get(symbol=stock_symbol)
        except Stock.DoesNotExist:
            # Create mock stock
            stock = Stock.objects.create(
                symbol=stock_symbol,
                name=f"{stock_symbol} Corp.",
                current_price=purchase_price * (1 + (hash(stock_symbol) % 10 - 5) / 100)
            )
        
        # Get or create portfolio entry
        portfolio, created = Portfolio.objects.get_or_create(
            user=request.user,
            stock=stock,
            defaults={
                'shares': shares,
                'average_buy_price': purchase_price
            }
        )
        
        if not created:
            # Update existing position
            total_shares = portfolio.shares + shares
            total_cost = (portfolio.shares * portfolio.average_buy_price) + (shares * purchase_price)
            portfolio.shares = total_shares
            portfolio.average_buy_price = total_cost / total_shares
            portfolio.save()
        
        # Create transaction record
        PortfolioTransaction.objects.create(
            user=request.user,
            stock=stock,
            transaction_type='buy',
            shares=shares,
            price_per_share=purchase_price
        )
        
        return Response({
            'status': 'success',
            'data': PortfolioSerializer(portfolio).data,
            'message': f'{stock_symbol} added to portfolio'
        }, status=status.HTTP_201_CREATED)


class RemovePortfolioView(generics.DestroyAPIView):
    """Remove stock from portfolio"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        try:
            portfolio = self.get_object()
            stock_symbol = portfolio.stock.symbol
            portfolio.delete()
            
            return Response({
                'status': 'success',
                'message': f'{stock_symbol} removed from portfolio'
            })
        except:
            return Response({
                'status': 'error',
                'message': 'Portfolio item not found'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portfolio_summary_view(request):
    """Get portfolio summary"""
    user = request.user
    
    holdings = Portfolio.objects.filter(user=user)
    
    # Calculate totals
    total_value = sum(h.current_value for h in holdings)
    total_cost = sum(h.cost_basis for h in holdings)
    day_change = sum(h.day_change for h in holdings)
    
    total_gain_loss = total_value - total_cost
    total_gain_loss_pct = round((total_gain_loss / total_cost) * 100, 2) if total_cost > 0 else 0
    day_change_pct = round((day_change / (total_value - day_change)) * 100, 2) if total_value > day_change else 0
    
    # Determine risk level
    analytics, _ = PortfolioAnalytics.objects.get_or_create(user=user)
    risk_score = float(analytics.risk_score)
    
    if risk_score < 40:
        risk_level = 'Low'
    elif risk_score < 70:
        risk_level = 'Moderate'
    else:
        risk_level = 'High'
    
    data = {
        'total_value': round(total_value, 2),
        'total_cost': round(total_cost, 2),
        'total_gain_loss': round(total_gain_loss, 2),
        'total_gain_loss_percentage': total_gain_loss_pct,
        'day_gain_loss': round(day_change, 2),
        'day_gain_loss_percentage': day_change_pct,
        'number_of_holdings': holdings.count(),
        'risk_level': risk_level,
        'risk_score': risk_score
    }
    
    return Response({
        'status': 'success',
        'data': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portfolio_analytics_view(request):
    """Get portfolio analytics"""
    user = request.user
    
    holdings = Portfolio.objects.filter(user=user)
    
    # Calculate analytics
    analytics, _ = PortfolioAnalytics.objects.get_or_create(user=user)
    
    # Calculate sector allocation
    sector_allocation = {}
    for holding in holdings:
        sector = holding.stock.sector or 'Other'
        value = float(holding.current_value)
        if sector in sector_allocation:
            sector_allocation[sector] += value
        else:
            sector_allocation[sector] = value
    
    # Calculate diversification score (0-100)
    total_value = sum(sector_allocation.values())
    if total_value > 0 and len(sector_allocation) > 0:
        # Higher score for more sectors and more balanced allocation
        num_sectors = len(sector_allocation)
        avg_allocation = total_value / num_sectors if num_sectors > 0 else 0
        variance = sum((v - avg_allocation) ** 2 for v in sector_allocation.values()) / num_sectors
        diversification = min(100, (num_sectors * 10) + (50 - min(50, variance / 1000000)))
    else:
        diversification = 0
    
    analytics.sector_allocation = sector_allocation
    analytics.diversification_score = round(diversification, 2)
    
    # Calculate volatility (mock)
    analytics.volatility = round(18.5, 2)
    analytics.beta = round(1.12, 2)
    analytics.sharpe_ratio = round(1.45, 2)
    
    analytics.save()
    
    # Additional metrics
    additional_metrics = {
        'volatility': f"{analytics.volatility}%",
        'diversification': f"Good ({len(sector_allocation)} sectors)" if len(sector_allocation) >= 5 else f"Fair ({len(sector_allocation)} sectors)",
        'beta': analytics.beta,
        'sharpe_ratio': analytics.sharpe_ratio
    }
    
    return Response({
        'status': 'success',
        'data': {
            'analytics': PortfolioAnalyticsSerializer(analytics).data,
            'additional_metrics': additional_metrics
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portfolio_allocation_view(request):
    """Get portfolio allocation data for charts"""
    user = request.user
    holdings = Portfolio.objects.filter(user=user)
    
    labels = []
    data = []
    colors = [
        '#00d4ff', '#3b82f6', '#8b5cf6', '#10b981',
        '#f59e0b', '#ef4444', '#ec4899', '#6366f1'
    ]
    
    for i, holding in enumerate(holdings):
        labels.append(holding.stock.symbol)
        data.append(float(holding.current_value))
    
    return Response({
        'status': 'success',
        'data': {
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)]
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portfolio_performance_view(request):
    """Get portfolio performance history"""
    user = request.user
    days = int(request.query_params.get('days', 30))
    
    # Generate performance data
    labels = []
    values = []
    
    base_value = 100000
    for i in range(days, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        labels.append(date.strftime('%b %d'))
        
        # Generate realistic growth curve
        change = (i % 5 - 2) * 500 + (hash(date.strftime('%Y%m%d')) % 1000 - 500)
        value = base_value + change + (days - i) * 200
        values.append(round(value, 2))
    
    return Response({
        'status': 'success',
        'data': {
            'labels': labels,
            'values': values
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portfolio_transactions_view(request):
    """Get portfolio transaction history"""
    transactions = PortfolioTransaction.objects.filter(
        user=request.user
    ).order_by('-transaction_date')[:50]
    
    return Response({
        'status': 'success',
        'data': PortfolioTransactionSerializer(transactions, many=True).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_portfolio_view(request):
    """Export portfolio data"""
    holdings = Portfolio.objects.filter(user=request.user)
    
    data = []
    for holding in holdings:
        data.append({
            'symbol': holding.stock.symbol,
            'name': holding.stock.name,
            'shares': float(holding.shares),
            'avg_price': float(holding.average_buy_price),
            'current_price': float(holding.stock.current_price),
            'market_value': float(holding.current_value),
            'gain_loss': float(holding.gain_loss),
            'gain_loss_pct': holding.gain_loss_percentage
        })
    
    return Response({
        'status': 'success',
        'data': data,
        'filename': f'portfolio_export_{timezone.now().strftime("%Y%m%d")}.csv'
    })
