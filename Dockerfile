# Use uma imagem base oficial do Python
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Define variáveis de ambiente para o Django
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copia o arquivo requirements.txt e instala as dependências
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o diretório de trabalho
COPY . /app/

# Aplica as migrações do banco de dados
# Certifique-se de que seu banco de dados PostgreSQL esteja acessível a partir do contêiner
# e que as credenciais em settings.py estejam corretas.
RUN python manage.py makemigrations wallet_app
RUN python manage.py migrate

# Comando para iniciar o servidor Django
# O servidor será acessível na porta 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Exponha a porta 8000
EXPOSE 8000
