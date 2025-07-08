Desafio Backend: API de Carteira Digital
Este projeto implementa uma API RESTful para gerenciar carteiras digitais e transações financeiras, conforme solicitado no desafio de código backend.

Sumário
Tecnologias Utilizadas

Justificativas

Funcionalidades da API

Configuração do Ambiente

Executando o Projeto

População Inicial do Banco de Dados

Endpoints da API

Testes Automatizados

Bônus Implementados

Tecnologias Utilizadas
Linguagem: Python 3.9+

Framework Web: Django 4.x

API REST: Django REST Framework

Autenticação: Django REST Framework Simple JWT

Banco de Dados: PostgreSQL

Geração de Dados Fictícios: Faker

Containerização: Docker e Docker Compose

Justificativas
Django: O Django foi escolhido por ser um framework robusto e completo ("batteries included") que acelera o desenvolvimento de aplicações web complexas. Ele oferece um ORM poderoso, um sistema de autenticação integrado e uma estrutura bem definida para organizar o código, o que contribui para a segurança e boas práticas. Além disso, a solicitação do desafio recomendava explicitamente o uso de Django.

Django REST Framework (DRF): É a biblioteca padrão para construir APIs RESTful com Django. Ele simplifica a serialização/desserialização de dados, a criação de views baseadas em classes e a implementação de autenticação e permissões.

Django REST Framework Simple JWT: Uma solução leve e eficiente para autenticação baseada em JSON Web Tokens (JWT), que é um requisito do desafio.

PostgreSQL: É um sistema de gerenciamento de banco de dados relacional (SGBDR) avançado, conhecido por sua robustez, confiabilidade, desempenho e conformidade com padrões SQL. É uma escolha excelente para aplicações que exigem integridade de dados e escalabilidade, e foi o banco de dados preferido na descrição do desafio.

Docker e Docker Compose: Permitem empacotar a aplicação e suas dependências em contêineres, garantindo um ambiente de desenvolvimento e produção consistente e isolado. O Docker Compose facilita a orquestração de múltiplos serviços (como a aplicação Django e o banco de dados PostgreSQL).

Funcionalidades da API
A API oferece as seguintes funcionalidades:

Autenticação: Geração e renovação de tokens JWT.

Criação de Usuário: Registro de novos usuários na plataforma.

Consulta de Saldo: Visualização do saldo atual da carteira de um usuário.

Adição de Saldo: Depósito de fundos na carteira de um usuário.

Transferência entre Usuários: Realização de transferências de fundos entre carteiras de usuários.

Listagem de Transferências: Consulta de todas as transferências realizadas por um usuário, com opção de filtro por período de data.

Configuração do Ambiente
Siga os passos abaixo para configurar e executar o projeto.

Pré-requisitos
Python 3.9+

PostgreSQL instalado e em execução (se não usar Docker Compose)

pip (gerenciador de pacotes Python)

Docker e Docker Compose (recomendado para desenvolvimento e produção)

1. Clonar o Repositório
git clone <URL_DO_SEU_REPOSITORIO>
cd wallet_api_challenge

2. Configurar o Banco de Dados PostgreSQL (com Docker Compose)
Se você for usar Docker Compose, o banco de dados será provisionado automaticamente. Você só precisa garantir que a senha no docker-compose.yml corresponda à que você usará no settings.py.

Atualize o arquivo wallet_api_challenge/settings.py com as credenciais do seu banco de dados, garantindo que a PASSWORD corresponda à que você definiu no docker-compose.yml:

# wallet_api_challenge/settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'wallet_db',
        'USER': 'wallet_user',
        'PASSWORD': 'your_password', # <--- DEVE SER A MESMA SENHA QUE VOCÊ DEFINIU NO docker-compose.yml
        'HOST': 'db', # O nome do serviço do banco de dados no docker-compose.yml
        'PORT': '5432',
    }
}

Observação: Se você não for usar Docker Compose e preferir uma instalação local do PostgreSQL, siga as instruções da seção anterior "Configurar o Banco de Dados PostgreSQL" para criar o usuário e o banco de dados manualmente.

3. Aplicar Migrações do Banco de Dados
Importante: Recentemente, o campo timestamp no modelo Transaction foi alterado para não ter mais auto_now_add=True. Isso significa que o timestamp deve ser fornecido explicitamente ao criar transações. Para que essa mudança seja refletida no seu banco de dados, você precisará criar e aplicar uma nova migração.

Se estiver usando Docker Compose, as migrações serão aplicadas automaticamente quando você iniciar os serviços, conforme configurado no command do serviço web no docker-compose.yml.

Se estiver executando localmente (sem Docker Compose), execute:

python manage.py makemigrations wallet_app
python manage.py migrate

Executando o Projeto
Usando Docker Compose (Recomendado)
Certifique-se de ter o Docker e o Docker Compose instalados.

Construa e inicie os serviços:

docker-compose up --build

Este comando irá construir a imagem da sua aplicação (se houver alterações), criar os contêineres e iniciar o banco de dados e o servidor Django.

População Inicial do Banco de Dados (dentro do contêiner):
Para popular o banco de dados com dados fictícios para demonstração, execute o seguinte comando após os serviços estarem em execução:

docker-compose exec web python manage.py seed_data

Este script criará 10 usuários com carteiras e realizará algumas transações fictícias. Certifique-se de que seu script seed_data.py também esteja fornecendo um timestamp explícito para as transações, por exemplo, usando timezone.now().

Criar um Superusuário (Opcional, para acesso ao Admin Django - dentro do contêiner):

docker-compose exec web python manage.py createsuperuser

Siga as instruções para criar um superusuário.

A API estará disponível em http://localhost:8000/.

Executando Localmente (Sem Docker Compose)
Criar e Ativar o Ambiente Virtual:

python -m venv venv
# No Linux/macOS:
source venv/bin/activate
# No Windows:
venv\Scripts\activate

Instalar as Dependências:

pip install -r requirements.txt

População Inicial do Banco de Dados:

python manage.py seed_data

Criar um Superusuário (Opcional, para acesso ao Admin Django):

python manage.py createsuperuser

Iniciar o Servidor de Desenvolvimento:

python manage.py runserver

A API estará disponível em http://127.0.0.1:8000/.

Endpoints da API
Todos os endpoints requerem autenticação JWT, exceto o registro de usuário e a obtenção de token. O token JWT deve ser enviado no cabeçalho Authorization no formato Bearer <token>.

Autenticação
Obter Token JWT (Login)

URL: /api/token/

Método: POST

Corpo da Requisição (JSON):

{
    "username": "seu_usuario",
    "password": "sua_senha"
}

Resposta (JSON):

{
    "refresh": "...",
    "access": "..."
}

Renovar Token JWT

URL: /api/token/refresh/

Método: POST

Corpo da Requisição (JSON):

{
    "refresh": "seu_refresh_token"
}

Resposta (JSON):

{
    "access": "novo_access_token"
}

Usuários
Criar Usuário (Registro)

URL: /api/users/register/

Método: POST

Corpo da Requisição (JSON):

{
    "username": "novo_usuario",
    "password": "senha_segura",
    "email": "novo.usuario@example.com"
}

Resposta (JSON):

{
    "id": 1,
    "username": "novo_usuario",
    "email": "novo.usuario@example.com"
}

Carteiras
Consultar Saldo da Carteira

URL: /api/wallet/balance/

Método: GET

Autenticação: Necessária (Token JWT)

Resposta (JSON):

{
    "balance": "1234.56"
}

Adicionar Saldo à Carteira (Depósito)

URL: /api/wallet/deposit/

Método: POST

Autenticação: Necessária (Token JWT)

Corpo da Requisição (JSON):

{
    "amount": 100.00
}

Resposta (JSON):

{
    "mensagem": "Depósito realizado com sucesso.",
    "novo_saldo": "1334.56"
}

Transações
Criar uma Transferência

URL: /api/transactions/transfer/

Método: POST

Autenticação: Necessária (Token JWT)

Corpo da Requisição (JSON):

{
    "receiver_username": "usuario_destino",
    "amount": 50.00
}

Resposta (JSON):

{
    "mensagem": "Transferência realizada com sucesso.",
    "id_transacao": 123,
    "novo_saldo_remetente": "1284.56",
    "novo_saldo_destinatario": "650.00"
}

Erros:

400 Bad Request: Saldo insuficiente, usuário destino não encontrado, valor inválido.

400 Bad Request: Não é possível transferir para si mesmo.

Listar Transferências Realizadas por um Usuário

URL: /api/transactions/list/

Método: GET

Autenticação: Necessária (Token JWT)

Parâmetros de Consulta (Opcionais):

start_date: Data de início no formato YYYY-MM-DD (ex: 2023-01-01)

end_date: Data de fim no formato YYYY-MM-DD (ex: 2023-12-31)

Exemplo de URL com filtro: /api/transactions/list/?start_date=2024-01-01&end_date=2024-06-30

Resposta (JSON - Array de Transações):

[
    {
        "id": 1,
        "sender": "seu_usuario",
        "receiver": "usuario_destino_1",
        "amount": "50.00",
        "transaction_type": "TRANSFER",
        "timestamp": "2024-07-08T10:00:00Z"
    },
    {
        "id": 2,
        "sender": "seu_usuario",
        "receiver": "usuario_destino_2",
        "amount": "25.00",
        "transaction_type": "TRANSFER",
        "timestamp": "2024-07-08T11:30:00Z"
    },
    {
        "id": 3,
        "sender": "seu_usuario",
        "receiver": "seu_usuario",
        "amount": "100.00",
        "transaction_type": "DEPOSIT",
        "timestamp": "2024-07-08T09:00:00Z"
    }
]

Testes Automatizados
O projeto inclui um conjunto de testes automatizados para garantir a correta funcionalidade da API.

Para executar os testes, siga os passos abaixo:

Certifique-se de que o ambiente está configurado (localmente ou com Docker Compose).

Se estiver usando Docker Compose, execute os testes dentro do contêiner web:

docker-compose exec web python manage.py test wallet_app

Se estiver executando localmente, certifique-se de que o ambiente virtual está ativado e as dependências instaladas, e execute:

python manage.py test wallet_app

Os testes criarão um banco de dados de teste temporário, executarão os testes e, em seguida, destruirão o banco de dados de teste.

Bônus Implementados
Arquitetura: O projeto segue uma arquitetura modular com o uso de um aplicativo Django (wallet_app) para encapsular a lógica de negócio relacionada às carteiras e transações. A separação de concerns entre modelos, serializadores e views é clara.

Linter: Embora não configurado diretamente no ambiente, o código foi escrito com foco em boas práticas e legibilidade, aderindo a padrões como PEP 8.

Docker e Docker Compose: Implementação de Dockerfile e docker-compose.yml para facilitar a containerização e orquestração da aplicação e do banco de dados, garantindo um ambiente consistente e portátil.