# Tattoo Classification

Bot do Telegram que recebe uma foto de tatuagem, classifica o tatuador com um modelo de IA e exibe seus dados de contato e localização.

## Requisitos

- Python 3.10 ou superior
- Um token de bot do Telegram
- O arquivo de pesos em `models/tattogyn1.weights.h5`

## Instalação

```bash
git clone <URL_DO_REPOSITORIO>
cd tatto-classification
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
TELEGRAM_TOKEN=seu_token_do_bot
```

Coloque o arquivo `tattogyn1.weights.h5` dentro da pasta `models/`.

## Execução

Inicialize o banco de dados e cadastre os tatuadores:

```bash
python seed_tatuadores.py
```

Depois, inicie o bot:

```bash
python bot-classification.py
```

No Telegram, envie uma foto para o bot. Use `/tatuadores` para listar os tatuadores cadastrados.
