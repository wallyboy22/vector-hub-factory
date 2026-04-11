---
name: html_app_factory
description: Padrão para criar novos apps HTML+FastAPI no vector-hub-factory com fidelidade visual ao ui/index.html de referência.
---

# html_app_factory — Skill

Use esta skill ao criar qualquer novo frontend HTML para o projeto.

## Regra #1 — Nunca partir do zero
Sempre copie `ROOT/ui/index.html` como ponto de partida e modifique.
Nunca crie um HTML novo sem ler o original primeiro.

## Regra #2 — CSS compartilhado
Todo HTML novo deve ter no `<head>`:
```html
<link rel="stylesheet" href="/assets/shared.css">
<script src="/assets/config.js"></script>
```
Nunca copiar `<style>` inline — usar o compartilhado.

## Regra #3 — URLs via config.js
Nunca hardcode `http://localhost:8000`. Usar sempre:
```javascript
const apiUrl = window.VHF_CONFIG.API_URL;
```

## Regra #4 — Registrar no api.py
Todo novo HTML precisa de uma rota GET no `src/api.py`:
```python
@app.get("/novo-app")
def novo_app():
    return FileResponse("ui/novo-app/index.html")
```

## Regra #5 — Testar sem servidor
A vitrine (`ui/vitrina/index.html`) deve abrir sem backend.
Os chatbots (`ui/index.html`, `ui/cross/index.html`) precisam do uvicorn rodando.

## Checklist antes de entregar um novo app HTML

- [ ] Copiou `ui/index.html` como base
- [ ] Usa `/assets/shared.css` (não tem `<style>` inline)
- [ ] Usa `window.VHF_CONFIG.API_URL` para todas as chamadas de API
- [ ] Tem rota GET registrada no `src/api.py`
- [ ] Testou no browser sem erros no console
- [ ] Aparência visual idêntica ao chatbot original (mesma fonte, cores, layout)