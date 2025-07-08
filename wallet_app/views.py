from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ParseError
from django.contrib.auth.models import User
from django.db import transaction, models
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Wallet, Transaction
from .serializers import (
    UserSerializer,
    WalletSerializer,
    DepositSerializer,
    TransferSerializer,
    TransactionSerializer
)

class UserCreateView(generics.CreateAPIView):
    """
    View para criar um novo usuário (registro).
    Não requer autenticação.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [] # Permite acesso sem autenticação

class WalletBalanceView(APIView):
    """
    View para consultar o saldo da carteira do usuário autenticado.
    Requer autenticação.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retorna o saldo da carteira do usuário logado.
        """
        try:
            wallet = request.user.wallet
            serializer = WalletSerializer(wallet)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Wallet.DoesNotExist:
            return Response({"erro": "Carteira não encontrada para este usuário."},
                            status=status.HTTP_404_NOT_FOUND)

class WalletDepositView(APIView):
    """
    View para adicionar saldo à carteira do usuário autenticado (depósito).
    Requer autenticação.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Processa um depósito na carteira do usuário.
        """
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']

            with transaction.atomic(): # Garante atomicidade da operação
                wallet = request.user.wallet
                wallet.balance += amount
                wallet.save()

                # Registra a transação de depósito
                Transaction.objects.create(
                    sender=request.user, # O próprio usuário é o remetente (para depósitos)
                    receiver=request.user,
                    amount=amount,
                    transaction_type='DEPOSIT',
                    timestamp=timezone.now() # Adicionado explicitamente
                )
            return Response(
                {"mensagem": "Depósito realizado com sucesso.", "novo_saldo": wallet.balance},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransferCreateView(APIView):
    """
    View para criar uma transferência entre usuários.
    Requer autenticação.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Processa uma transferência de fundos entre duas carteiras de usuários.
        """
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            receiver_username = serializer.validated_data['receiver_username']
            amount = serializer.validated_data['amount']
            sender_user = request.user

            # Não permitir transferência para si mesmo
            if sender_user.username == receiver_username:
                return Response(
                    {"erro": "Não é possível transferir para si mesmo."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                receiver_user = User.objects.get(username=receiver_username)
            except User.DoesNotExist:
                return Response(
                    {"erro": "Usuário destinatário não encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )

            with transaction.atomic(): # Garante atomicidade da operação
                sender_wallet = sender_user.wallet
                receiver_wallet = receiver_user.wallet

                if sender_wallet.balance < amount:
                    return Response(
                        {"erro": "Saldo insuficiente para realizar a transferência."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                sender_wallet.balance -= amount
                receiver_wallet.balance += amount

                sender_wallet.save()
                receiver_wallet.save()

                # Registra a transação de transferência
                new_transaction = Transaction.objects.create(
                    sender=sender_user,
                    receiver=receiver_user,
                    amount=amount,
                    transaction_type='TRANSFER',
                    timestamp=timezone.now() # Adicionado explicitamente
                )
            return Response(
                {
                    "mensagem": "Transferência realizada com sucesso.",
                    "id_transacao": new_transaction.id,
                    "novo_saldo_remetente": sender_wallet.balance,
                    "novo_saldo_destinatario": receiver_wallet.balance
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionListView(generics.ListAPIView):
    """
    View para listar as transações de um usuário, com filtro opcional por período de data.
    Requer autenticação.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna as transações onde o usuário é remetente ou destinatário.
        Permite filtrar por start_date e end_date.
        """
        user = self.request.user
        queryset = Transaction.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).distinct()

        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                raise ParseError(detail="Formato de data inválido para 'start_date'. Use AAAA-MM-DD.")

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                raise ParseError(detail="Formato de data inválido para 'end_date'. Use AAAA-MM-DD.")

        return queryset.order_by('-timestamp')
