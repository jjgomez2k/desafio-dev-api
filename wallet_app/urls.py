from django.urls import path
from .views import (
    UserCreateView,
    WalletBalanceView,
    WalletDepositView,
    TransferCreateView,
    TransactionListView
)

urlpatterns = [
    # Rotas de Usuário
    path('users/register/', UserCreateView.as_view(), name='user_register'),

    # Rotas de Carteira
    path('wallet/balance/', WalletBalanceView.as_view(), name='wallet_balance'),
    path('wallet/deposit/', WalletDepositView.as_view(), name='wallet_deposit'),

    # Rotas de Transação
    path('transactions/transfer/', TransferCreateView.as_view(), name='transaction_transfer'),
    path('transactions/list/', TransactionListView.as_view(), name='transaction_list'),
]
