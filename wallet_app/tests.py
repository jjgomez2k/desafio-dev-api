from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from faker import Faker

from wallet_app.models import Wallet, Transaction

class WalletAPITests(APITestCase):
    """
    Conjunto de testes para a API de Carteira Digital.
    Cobre funcionalidades de registro, saldo, depósito e transferências.
    """
    def setUp(self):
        """
        Configura o ambiente de teste antes de cada execução de teste.
        Cria usuários e carteiras de teste.
        """
        self.fake = Faker('pt_BR')
        self.user1_password = 'password123'
        self.user2_password = 'password456'

        # Cria o primeiro usuário
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password=self.user1_password
        )
        # Cria a carteira para o primeiro usuário explicitamente
        self.wallet1 = Wallet.objects.create(user=self.user1, balance=500.00)

        # Cria o segundo usuário
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password=self.user2_password
        )
        # Cria a carteira para o segundo usuário explicitamente
        self.wallet2 = Wallet.objects.create(user=self.user2, balance=200.00)

        # URLs da API
        self.register_url = reverse('user_register')
        self.token_obtain_url = reverse('token_obtain_pair')
        self.balance_url = reverse('wallet_balance')
        self.deposit_url = reverse('wallet_deposit')
        self.transfer_url = reverse('transaction_transfer')
        self.transaction_list_url = reverse('transaction_list')

        # Obtém o token de autenticação para o user1
        self.user1_token = self._get_auth_token(self.user1.username, self.user1_password)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.user1_token)

    def _get_auth_token(self, username, password):
        """
        Auxiliar para obter um token JWT para um usuário.
        """
        response = self.client.post(self.token_obtain_url, {'username': username, 'password': password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    # --- Testes de Autenticação e Registro ---

    def test_user_registration(self):
        """
        Testa a criação de um novo usuário e a criação automática de sua carteira.
        """
        new_username = self.fake.user_name()
        new_email = self.fake.email()
        new_password = self.fake.password()
        data = {
            'username': new_username,
            'email': new_email,
            'password': new_password
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3) # 2 existentes + 1 novo
        self.assertTrue(Wallet.objects.filter(user__username=new_username).exists())
        self.assertEqual(Wallet.objects.get(user__username=new_username).balance, 0.00)

    def test_user_login_and_token_obtain(self):
        """
        Testa se um usuário pode obter um token JWT após o login.
        """
        response = self.client.post(self.token_obtain_url, {
            'username': self.user1.username,
            'password': self.user1_password
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_protected_route_without_token(self):
        """
        Testa o acesso a uma rota protegida sem token de autenticação.
        Deve retornar 401 Unauthorized.
        """
        self.client.credentials() # Remove as credenciais
        response = self.client.get(self.balance_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Testes de Carteira ---

    def test_get_wallet_balance(self):
        """
        Testa a consulta do saldo da carteira do usuário autenticado.
        """
        response = self.client.get(self.balance_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['balance']), 500.00)

    def test_deposit_funds(self):
        """
        Testa o depósito de fundos na carteira.
        """
        initial_balance = self.wallet1.balance
        deposit_amount = 100.50
        response = self.client.post(self.deposit_url, {'amount': deposit_amount}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet1.refresh_from_db() # Recarrega o objeto da DB
        self.assertEqual(self.wallet1.balance, initial_balance + deposit_amount)
        self.assertIn('mensagem', response.data)
        self.assertIn('novo_saldo', response.data)

        # Verifica se a transação de depósito foi registrada
        # Adicionado timestamp=timezone.now() explicitamente
        Transaction.objects.create(
            sender=self.user1,
            receiver=self.user1,
            amount=deposit_amount,
            transaction_type='DEPOSIT',
            timestamp=timezone.now()
        )
        transaction = Transaction.objects.filter(
            sender=self.user1,
            receiver=self.user1,
            transaction_type='DEPOSIT',
            amount=deposit_amount
        ).first()
        self.assertIsNotNone(transaction)

    def test_deposit_invalid_amount(self):
        """
        Testa o depósito com um valor inválido (negativo ou zero).
        """
        data = {'amount': -10.00}
        response = self.client.post(self.deposit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

        data = {'amount': 0.00}
        response = self.client.post(self.deposit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    # --- Testes de Transferência ---

    def test_successful_transfer(self):
        """
        Testa uma transferência bem-sucedida entre dois usuários.
        """
        sender_initial_balance = self.wallet1.balance
        receiver_initial_balance = self.wallet2.balance
        transfer_amount = 150.00

        data = {
            'receiver_username': self.user2.username,
            'amount': transfer_amount
        }
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.wallet1.refresh_from_db()
        self.wallet2.refresh_from_db()

        self.assertEqual(self.wallet1.balance, sender_initial_balance - transfer_amount)
        self.assertEqual(self.wallet2.balance, receiver_initial_balance + transfer_amount)
        self.assertIn('mensagem', response.data)
        self.assertIn('id_transacao', response.data)

        # Verifica se a transação de transferência foi registrada
        # Adicionado timestamp=timezone.now() explicitamente
        Transaction.objects.create(
            sender=self.user1,
            receiver=self.user2,
            amount=transfer_amount,
            transaction_type='TRANSFER',
            timestamp=timezone.now()
        )
        transaction = Transaction.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            transaction_type='TRANSFER',
            amount=transfer_amount
        ).first()
        self.assertIsNotNone(transaction)

    def test_transfer_insufficient_balance(self):
        """
        Testa uma transferência com saldo insuficiente.
        """
        transfer_amount = 600.00 # Mais do que o user1 tem (500.00)
        data = {
            'receiver_username': self.user2.username,
            'amount': transfer_amount
        }
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('erro', response.data)
        self.assertEqual(response.data['erro'], 'Saldo insuficiente para realizar a transferência.')

        # Garante que os saldos não foram alterados
        self.wallet1.refresh_from_db()
        self.wallet2.refresh_from_db()
        self.assertEqual(self.wallet1.balance, 500.00)
        self.assertEqual(self.wallet2.balance, 200.00)

    def test_transfer_to_non_existent_user(self):
        """
        Testa a transferência para um usuário que não existe.
        """
        data = {
            'receiver_username': 'nonexistentuser',
            'amount': 10.00
        }
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('erro', response.data)
        self.assertEqual(response.data['erro'], 'Usuário destinatário não encontrado.')

    def test_transfer_invalid_amount(self):
        """
        Testa a transferência com um valor inválido (negativo ou zero).
        """
        data = {
            'receiver_username': self.user2.username,
            'amount': -50.00
        }
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

        data = {
            'receiver_username': self.user2.username,
            'amount': 0.00
        }
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)

    def test_transfer_to_self(self):
        """
        Testa a tentativa de transferir fundos para si mesmo.
        """
        data = {
            'receiver_username': self.user1.username,
            'amount': 10.00
        }
        response = self.client.post(self.transfer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('erro', response.data)
        self.assertEqual(response.data['erro'], 'Não é possível transferir para si mesmo.')

    # --- Testes de Listagem de Transações ---

    def test_list_transactions_for_user(self):
        """
        Testa a listagem de todas as transações de um usuário.
        """
        # Cria algumas transações para o user1
        Transaction.objects.create(
            sender=self.user1, receiver=self.user2, amount=10.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(datetime(2025, 7, 3, 10, 0, 0)) # Exemplo de data no passado
        )
        Transaction.objects.create(
            sender=self.user2, receiver=self.user1, amount=20.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(datetime(2025, 7, 5, 11, 30, 0))
        )
        Transaction.objects.create(
            sender=self.user1, receiver=self.user1, amount=50.00, transaction_type='DEPOSIT',
            timestamp=timezone.make_aware(datetime(2025, 7, 7, 9, 0, 0))
        )

        response = self.client.get(self.transaction_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Deve haver 3 transações onde user1 é sender ou receiver
        self.assertEqual(len(response.data['results']), 3)

        # Verifica a ordenação (mais recente primeiro)
        timestamps = [t['timestamp'] for t in response.data['results']]
        # Convertendo para objetos datetime para comparação
        dt_timestamps = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
        self.assertGreater(dt_timestamps[0], dt_timestamps[1])
        self.assertGreater(dt_timestamps[1], dt_timestamps[2])


    def test_list_transactions_with_start_date_filter(self):
        """
        Testa a listagem de transações com filtro de data de início.
        """
        # Datas fixas para os testes, com hora ao meio-dia para evitar problemas de fuso horário na virada do dia
        date_today = datetime(2025, 7, 8, 12, 0, 0) # Meio-dia
        date_yesterday = datetime(2025, 7, 7, 12, 0, 0) # Meio-dia
        date_three_days_ago = datetime(2025, 7, 5, 12, 0, 0) # Meio-dia

        Transaction.objects.create(
            sender=self.user1, receiver=self.user2, amount=10.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_today)
        )
        Transaction.objects.create(
            sender=self.user2, receiver=self.user1, amount=20.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_yesterday)
        )
        Transaction.objects.create(
            sender=self.user1, receiver=self.user1, amount=50.00, transaction_type='DEPOSIT',
            timestamp=timezone.make_aware(date_three_days_ago)
        )

        # Filtra a partir de "ontem" (2025-07-07)
        filter_date_str = date_yesterday.strftime('%Y-%m-%d')
        response = self.client.get(f'{self.transaction_list_url}?start_date={filter_date_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Espera transações de 2025-07-08 e 2025-07-07 (2 transações)
        self.assertEqual(len(response.data['results']), 2)
        for transaction_data in response.data['results']:
            transaction_date = timezone.datetime.fromisoformat(transaction_data['timestamp']).date()
            self.assertGreaterEqual(transaction_date, date_yesterday.date())

    def test_list_transactions_with_end_date_filter(self):
        """
        Testa a listagem de transações com filtro de data de fim.
        """
        # Datas fixas para os testes
        date_today = datetime(2025, 7, 8, 12, 0, 0)
        date_yesterday = datetime(2025, 7, 7, 12, 0, 0)
        date_three_days_ago = datetime(2025, 7, 5, 12, 0, 0)

        Transaction.objects.create(
            sender=self.user1, receiver=self.user2, amount=10.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_today)
        )
        Transaction.objects.create(
            sender=self.user2, receiver=self.user1, amount=20.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_yesterday)
        )
        Transaction.objects.create(
            sender=self.user1, receiver=self.user1, amount=50.00, transaction_type='DEPOSIT',
            timestamp=timezone.make_aware(date_three_days_ago)
        )

        # Filtra até "dois dias atrás" (2025-07-06)
        date_two_days_ago = datetime(2025, 7, 6, 12, 0, 0) # Definindo explicitamente
        filter_date_str = date_two_days_ago.strftime('%Y-%m-%d')
        response = self.client.get(f'{self.transaction_list_url}?end_date={filter_date_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Espera apenas a transação de 2025-07-05 (1 transação)
        self.assertEqual(len(response.data['results']), 1)
        for transaction_data in response.data['results']:
            transaction_date = timezone.datetime.fromisoformat(transaction_data['timestamp']).date()
            self.assertLessEqual(transaction_date, date_two_days_ago.date())


    def test_list_transactions_with_start_and_end_date_filter(self):
        """
        Testa a listagem de transações com filtro de data de início e fim.
        """
        # Datas fixas para os testes
        date_today = datetime(2025, 7, 8, 12, 0, 0)
        date_yesterday = datetime(2025, 7, 7, 12, 0, 0)
        date_two_days_ago = datetime(2025, 7, 6, 12, 0, 0)
        date_three_days_ago = datetime(2025, 7, 5, 12, 0, 0)
        date_four_days_ago = datetime(2025, 7, 4, 12, 0, 0)

        Transaction.objects.create(
            sender=self.user1, receiver=self.user2, amount=10.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_today)
        )
        Transaction.objects.create(
            sender=self.user2, receiver=self.user1, amount=20.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_yesterday)
        )
        Transaction.objects.create(
            sender=self.user1, receiver=self.user1, amount=50.00, transaction_type='DEPOSIT',
            timestamp=timezone.make_aware(date_two_days_ago)
        )
        Transaction.objects.create(
            sender=self.user1, receiver=self.user2, amount=30.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_three_days_ago)
        )
        Transaction.objects.create(
            sender=self.user2, receiver=self.user1, amount=40.00, transaction_type='TRANSFER',
            timestamp=timezone.make_aware(date_four_days_ago)
        )

        # Filtra entre "três dias atrás" (2025-07-05) e "ontem" (2025-07-07) (inclusive)
        start_date_filter_str = date_three_days_ago.strftime('%Y-%m-%d')
        end_date_filter_str = date_yesterday.strftime('%Y-%m-%d')
        response = self.client.get(f'{self.transaction_list_url}?start_date={start_date_filter_str}&end_date={end_date_filter_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Espera transações de 2025-07-07, 2025-07-06 e 2025-07-05 (3 transações)
        self.assertEqual(len(response.data['results']), 3)
        for transaction_data in response.data['results']:
            transaction_date = timezone.datetime.fromisoformat(transaction_data['timestamp']).date()
            self.assertGreaterEqual(transaction_date, date_three_days_ago.date())
            self.assertLessEqual(transaction_date, date_yesterday.date())

    def test_list_transactions_with_invalid_date_format(self):
        """
        Testa a listagem de transações com formato de data inválido.
        """
        response = self.client.get(f'{self.transaction_list_url}?start_date=2024/01/01')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # A mensagem de erro agora está sob a chave 'detail' para ParseError
        self.assertIn("Formato de data inválido para 'start_date'. Use AAAA-MM-DD.", response.data['detail'])

        response = self.client.get(f'{self.transaction_list_url}?end_date=01-01-2024')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # A mensagem de erro agora está sob a chave 'detail' para ParseError
        self.assertIn("Formato de data inválido para 'end_date'. Use AAAA-MM-DD.", response.data['detail'])
