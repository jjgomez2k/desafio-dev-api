from django.db import models
from django.contrib.auth.models import User

class Wallet(models.Model):
    """
    Modelo para representar a carteira de um usuário.
    Cada usuário tem uma única carteira.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Carteira"
        verbose_name_plural = "Carteiras"

    def __str__(self):
        return f"Carteira de {self.user.username} - Saldo: {self.balance}"

class Transaction(models.Model):
    """
    Modelo para registrar transações financeiras (depósitos e transferências).
    """
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Depósito'),
        ('TRANSFER', 'Transferência'),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField() # Removido auto_now_add=True

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ['-timestamp'] # Ordena as transações mais recentes primeiro

    def __str__(self):
        if self.transaction_type == 'DEPOSIT':
            return f"Depósito de {self.amount} para {self.receiver.username} em {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        else:
            return f"Transferência de {self.amount} de {self.sender.username} para {self.receiver.username} em {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
