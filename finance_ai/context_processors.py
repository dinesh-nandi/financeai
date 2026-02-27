"""
Context processors for FinanceAI templates.
Exposes WalletConnect project ID for QR login on auth pages.
"""
from django.conf import settings


def walletconnect_config(request):
    """Add WalletConnect project ID for frontend QR login."""
    return {
        'walletconnect_project_id': getattr(settings, 'WALLETCONNECT_PROJECT_ID', '') or '',
    }
