# Arquivo Histórico — Vector Hub Factory

> Este documento consolida os planos anteriores que já foram **superados ou parcialmente implementados**.
> Serve apenas como referência de contexto.  
> **O plano ativo está em `PLANO.md`. As tasks estão em `TASKS.md`.**

---

## O que foi feito (Fases 0–5, T00–T14)

- ✅ Pipeline RAG completo: `src/chunker.py`, `src/embedder.py`, `src/vectorstore.py`, `src/qa.py`
- ✅ Backend FastAPI em `src/api.py` com rotas `/ask`, `/pdf`, `/reports`, `/health/v2`
- ✅ AppGuardian (`src/guardian.py`) com checagem de integridade e rotação de chaves
- ✅ CSS compartilhado em `ui/assets/shared.css`
- ✅ Config de URLs (`ui/assets/config.js`) com detecção local vs. produção
- ✅ Chatbot RAF (`ui/chatbot-raf/index.html`) — funcional mas com bugs de layout
- ✅ Chatbot RAD (`ui/chatbot-rad/index.html`) — idem
- ✅ Vitrine Workspace (`ui/vitrine/index.html`) — sidebar slim + iframe, mas com bugs visuais
- ✅ `tab-manager.js` criado em `ui/assets/tab-manager.js` — funcional mas integração quebrou o canvas

## Bugs conhecidos introduzidos na última sessão

1. **Canvas PDF sumiu no RAF/RAD:** O `TabManager` substitui o `innerHTML` do `#pdf-container` ao inicializar, mas o `#pdf-viewer` que existia no HTML foi destruído antes de ser referenciado no JS. O PDF nunca carrega.
2. **CSS conflitante no body:** `flex-direction: column` e `flex-direction: row` ambos declarados no mesmo seletor `body` — o último vence, quebrando o layout vertical.
3. **Sidebar com margens/ícones grandes:** `.slim-sidebar-item` com `padding: 12px 8px` e `font-size: 1.4rem` muito grande para uma sidebar de 52px.
4. **Hub (home.html) com paleta azul estranha:** `--primary-color: #00b4d8` destonando da identidade RAF/RAD.
5. **Gaveta Skills ainda presente** no HTML mas foi decidido remover.
6. **Botão Voltar ainda presente** no header do chatbot — deve ser removido (navegação só pela Sidebar).
7. **Multi-chat ainda listado** na sidebar — foi decidido remover.

## Decisões arquiteturais obsoletas

- ~~Streamlit para os chatbots~~ → descartado, uso apenas HTML+FastAPI
- ~~Multi-relatório como app separado~~ → descartado
- ~~Gaveta de Skills/Ferramentas~~ → descartado, complexidade desnecessária
- ~~Chatbots acessíveis standalone sem a vitrine~~ → descartado, acesso sempre pela Vitrine via sidebar
