// Vector Hub Factory — Configuração de URLs
// Edite apenas este arquivo para apontar para produção.
window.VHF_CONFIG = {
  // Servidor de API (backend para PDFs)
  API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://vector-hub-api.onrender.com',
    
  // Cloudflare Worker (proxy seguro para Gemini API)
  // Configure sua URL do Cloudflare Worker aqui
  WORKER_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8787'
    : 'https://vector-hub-worker.your-subdomain.workers.dev',
};