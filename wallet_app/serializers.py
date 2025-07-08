from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Wallet, Transaction

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para o modelo User.
    Usado para registrar novos usuários.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}} # Garante que a senha não seja retornada na resposta

    def create(self, validated_data):
        """
        Cria um novo usuário e sua carteira associada.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        Wallet.objects.create(user=user, balance=0.00) # Cria uma carteira com saldo inicial zero
        return user

class WalletSerializer(serializers.ModelSerializer):
    """
    Serializador para o modelo Wallet.
    """
    class Meta:
        model = Wallet
        fields = ['balance']

class DepositSerializer(serializers.Serializer):
    """
    Serializador para a entrada de dados de depósito.
    """
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)

class TransferSerializer(serializers.Serializer):
    """
    Serializador para a entrada de dados de transferência.
    """
    receiver_username = serializers.CharField(max_length=150)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)

class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializador para o modelo Transaction.
    Exibe o nome de usuário do remetente e do destinatário.
    """
    sender = serializers.CharField(source='sender.username', read_only=True)
    receiver = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'sender', 'receiver', 'amount', 'transaction_type', 'timestamp']
