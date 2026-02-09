# Deploy gratuito no Render (Bitrix24 Exporter)

Siga estes passos para colocar o sistema no ar no plano gratuito do Render.

## Pré-requisitos

1. **Código no GitHub**  
   - Crie um repositório no GitHub (se ainda não tiver).  
   - Envie o projeto: na pasta do projeto, execute:
     ```bash
     git init
     git add .
     git commit -m "Preparar deploy no Render"
     git branch -M main
     git remote add origin https://github.com/SEU_USUARIO/bitrix-exporter.git
     git push -u origin main
     ```
   - Substitua `SEU_USUARIO/bitrix-exporter` pelo seu repositório.

2. **Conta no Render**  
   - Acesse [render.com](https://render.com) e crie uma conta (pode usar login com GitHub).

---

## Deploy no Render

### Opção A: Usando o Blueprint (render.yaml)

1. Acesse [dashboard.render.com](https://dashboard.render.com).
2. Clique em **New** → **Blueprint**.
3. Conecte o repositório do GitHub (autorize o Render se pedir).
4. Selecione o repositório **bitrix-exporter** (ou o nome que você deu).
5. O Render vai detectar o `render.yaml`. Clique em **Apply**.
6. Nas variáveis de ambiente, informe:
   - **BITRIX_WEBHOOK_BASE**: a URL completa do seu webhook do Bitrix24 (ex.: `https://seu-portal.bitrix24.com.br/rest/1/xxxxx/`).
   - **SESSION_SECRET**: pode deixar o Render gerar automaticamente (já está configurado no Blueprint).
7. Clique em **Create Web Service**. O deploy vai começar.

### Opção B: Criar o serviço manualmente

1. Acesse [dashboard.render.com](https://dashboard.render.com).
2. Clique em **New** → **Web Service**.
3. Conecte o repositório do GitHub e escolha o repositório do **bitrix-exporter**.
4. Configure:
   - **Name**: `bitrix-exporter` (ou outro nome).
   - **Region**: escolha a mais próxima (ex.: Oregon ou Frankfurt).
   - **Branch**: `main`.
   - **Runtime**: **Python 3**.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Em **Environment**, adicione:
   - **BITRIX_WEBHOOK_BASE** = `https://seu-portal.bitrix24.com.br/rest/1/SEU_WEBHOOK/`  
     (substitua pela URL real do seu webhook.)
   - **SESSION_SECRET** = qualquer string longa e aleatória (ou use “Add Environment Variable” e deixe o Render gerar).
6. Em **Plan**, escolha **Free**.
7. Clique em **Create Web Service**. O primeiro deploy pode levar alguns minutos.

---

## Depois do deploy

- A URL do app será algo como: `https://bitrix-exporter.onrender.com` (o nome pode variar).
- **Plano gratuito:** após ~15 min sem acesso, o serviço entra em *sleep*. A primeira requisição depois disso pode levar até ~1 minuto (cold start).
- **Planilha de colaboradores:** a `Planilha de colaboradores.xlsx` que está no repositório será usada no Render. Para usar outra planilha (ex.: da sua área de trabalho), você precisaria configurar **COLABORADORES_PLANILHA** com uma URL acessível (ex.: link público de arquivo) ou manter a planilha atualizada no repo e dar push quando mudar.

---

## Resumo rápido

| Passo | Ação |
|-------|------|
| 1 | Código no GitHub |
| 2 | Render.com → New → Web Service (ou Blueprint) |
| 3 | Conectar repositório |
| 4 | Definir **BITRIX_WEBHOOK_BASE** (e opcionalmente **SESSION_SECRET**) |
| 5 | Plano **Free** → Create Web Service |
| 6 | Acessar a URL gerada e fazer login |

Se algo falhar no build ou no start, confira os **Logs** do serviço no Render; a mensagem de erro costuma indicar o que ajustar (por exemplo, variável de ambiente faltando).
