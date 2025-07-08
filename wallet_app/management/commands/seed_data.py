import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from faker import Faker

from wallet_app.models import Wallet, Transaction

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados fictícios de usuários, carteiras e transações.'

    def handle(self, *args, **kwargs):
        fake = Faker('pt_BR') # Usar localidade brasileira para nomes e emails

        self.stdout.write(self.style.SUCCESS('Iniciando a população de dados...'))

        # Limpa dados existentes (opcional, para testes)
        # User.objects.all().delete()
        # Wallet.objects.all().delete()
        # Transaction.objects.all().delete()

        num_users = 10
        num_transactions_per_user = 5
        users = []

        self.stdout.write(self.style.SUCCESS(f'Criando {num_users} usuários e carteiras...'))
        for i in range(num_users):
            username = fake.user_name() + str(i) # Garante unicidade
            email = fake.email()
            password = 'password123' # Senha padrão para usuários fictícios

            with transaction.atomic():
                user = User.objects.create_user(username=username, email=email, password=password)
                wallet = Wallet.objects.create(user=user, balance=round(random.uniform(100.00, 1000.00), 2))
                users.append(user)
                self.stdout.write(f'  - Usuário criado: {user.username} com saldo inicial: {wallet.balance}')

        self.stdout.write(self.style.SUCCESS('Criando transações fictícias...'))
        for user in users:
            self.stdout.write(f'  - Gerando transações para {user.username}...')
            for _ in range(num_transactions_per_user):
                # Decidir se é um depósito ou transferência
                is_deposit = random.choice([True, False])

                if is_deposit:
                    # Depósito
                    amount = round(random.uniform(10.00, 200.00), 2)
                    with transaction.atomic():
                        user_wallet = user.wallet
                        user_wallet.balance += amount
                        user_wallet.save()
                        Transaction.objects.create(
                            sender=user,
                            receiver=user,
                            amount=amount,
                            transaction_type='DEPOSIT',
                            timestamp=timezone.now() - timedelta(days=random.randint(1, 30)) # Transações nos últimos 30 dias
                        )
                    self.stdout.write(f'    - Depósito de {amount} para {user.username}')
                else:
                    # Transferência
                    # Tenta encontrar um destinatário diferente
                    possible_receivers = [u for u in users if u != user]
                    if not possible_receivers:
                        continue # Não há outros usuários para transferir

                    receiver_user = random.choice(possible_receivers)
                    amount = round(random.uniform(5.00, min(user.wallet.balance / 2, 150.00)), 2) # Limita o valor para evitar saldo negativo
                    if amount <= 0:
                        continue # Evita transferências de valor zero ou negativo

                    with transaction.atomic():
                        sender_wallet = user.wallet
                        receiver_wallet = receiver_user.wallet

                        if sender_wallet.balance >= amount:
                            sender_wallet.balance -= amount
                            receiver_wallet.balance += amount
                            sender_wallet.save()
                            receiver_wallet.save()
                            Transaction.objects.create(
                                sender=user,
                                receiver=receiver_user,
                                amount=amount,
                                transaction_type='TRANSFER',
                                timestamp=timezone.now() - timedelta(days=random.randint(1, 30))
                            )
                            self.stdout.write(f'    - Transferência de {amount} de {user.username} para {receiver_user.username}')
                        else:
                            self.stdout.write(f'    - Saldo insuficiente para {user.username} transferir {amount} para {receiver_user.username}. Saldo atual: {sender_wallet.balance}')

        self.stdout.write(self.style.SUCCESS('População de dados concluída!'))
        self.stdout.write(self.style.SUCCESS('Você pode usar os usuários criados (ex: username0, username1, etc.) com a senha "password123" para testar a API.'))
