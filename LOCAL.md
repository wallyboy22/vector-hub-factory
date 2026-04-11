# Vector Hub Factory - Teste Local

Com a nova arquitetura unificada, o servidor FastAPI (backend) também serve diretamente os arquivos estáticos (frontend). 

Isso significa que você não precisa mais levantar dois servidores separados para testar o aplicativo localmente.

## Como Iniciar (Completo)

Abra o terminal na raiz do projeto e execute:

```bash
# Se usar Windows e o ambiente virtual já tiver sido criado e ativado:
.\start_all.bat

# Comando alternativo (Funciona em Linux/Mac ou sem o .bat):
uvicorn src.api:app --port 8000 --reload
```

Depois, acesse no seu navegador: **http://localhost:8000**

## Arquitetura quando rodando local

| Serviço | URL |
|---------|-----|
| Frontend Vitrine (Hub) | http://localhost:8000/ |
| Chatbot RAF | http://localhost:8000/chatbot-raf |
| Chatbot RAD | http://localhost:8000/chatbot-rad |
| Multi-Relatório | http://localhost:8000/multi |
| Busca Transversal | http://localhost:8000/cross |
| API | http://localhost:8000/docs |

## Fluxo esperado

1. Abra **http://localhost:8000** → Você verá a Vitrine.
2. Navegue para qualquer chatbot pelos cartões na Vitrine.
3. Faça suas perguntas → A API nativa na porta 8000 retornará as respostas do RAG imediatamente.
4. Navegue nos PDFs inline.
5. Use os botões de "Voltar" ou "Início" para retornar à Vitrine central.