# ☁️ Deploy - Vector Hub Factory

## Estrutura

```
UI (GitHub Pages)     +     API (Cloudflare Workers)
├── Vitrine                   ├── Embeddings
├── Chatbot RAF               ├── Generate LLM
├── Chatbot RAD               └── (API keys protegidas)
├── Multi-Relatório
└── Busca Transversal
```

---

## 1. Cloudflare Workers (Backend Seguro)

### Requisitos
- Conta no [Cloudflare](https://dash.cloudflare.com)
- API Key do [Google AI Studio](https://aistudio.google.com/app/apikey)

### Deploy

```bash
# 1. Instale o Wrangler (CLI do Cloudflare)
npm install -g wrangler

# 2. Configure sua API key
wrangler secret put GOOGLE_API_KEY
# Cole sua API key quando solicitado

# 3. Faça deploy
cd worker
wrangler deploy
```

### Variáveis de Ambiente (opcional para .dev)
Edite `worker/.dev.vars` para desenvolvimento local:
```bash
GOOGLE_API_KEY=sua_api_key_aqui
```

### Teste local
```bash
wrangler dev
```

---

## 2. GitHub Pages (Frontend)

### Deploy automático
O workflow `.github/workflows/pages.yml` faz deploy automático a cada push na branch `main`.

### Deploy manual
```bash
git add .
git commit -m "Deploy: novos chatbots HTML"
git push origin main
```

Aguarde ~2 min para o GitHub Pages ficar disponível em:
`https://seu-usuario.github.io/vector-hub-factory/`

---

## 3. Configuração de URLs

Edite `ui/assets/config.js`:

```javascript
window.VHF_CONFIG = {
  // URL do seu Cloudflare Worker
  WORKER_URL: 'https://vector-hub-worker.seu-subdomain.workers.dev',
  
  // URL da API de PDFs (opcional - requer servidor)
  API_URL: 'https://seu-servidor.onrender.com'
};
```

---

## URLs Finais Esperadas

| Serviço | URL |
|---------|-----|
| Vitrine | `https://seu-user.github.io/vector-hub-factory/` |
| Chatbot RAF | `.../chatbot-raf/` |
| Chatbot RAD | `.../chatbot-rad/` |
| Multi | `.../multi/` |
| Cross-Search | `.../cross/` |
| Worker API | `https://xxx.workers.dev/` |

---

## Desenvolvimento Local

### Servidor de API (para PDFs)
```bash
uvicorn src.api:app --port 8000 --reload
```

### Frontend (para teste)
Use qualquer servidor HTTP:
```bash
# Python
python -m http.server 8080

# ou Node
npx serve .
```

Acesse: `http://localhost:8080`

---

## Solução de Problemas

### "API key não autorizada"
- Verifique se a API key está configurada no Cloudflare Workers
- Faça `wrangler secret list` para ver secrets configurados

### PDFs não carregam (GitHub Pages)
- Os PDFs requerem um servidor because GitHub Pages não suporta arquivos grandes
- Use o Cloudflare Workers para servir os PDFs, ou use um serviço como R2

### CORS errors
- Adicione seu domínio no CORS do Workers:
```javascript
const corsHeaders = {
  "Access-Control-Allow-Origin": "https://seu-user.github.io",
  // ...
};
```