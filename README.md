# 🏭 Vector Hub Factory

Uma plataforma modular de Ciência Aberta para transformar documentos científicos estáticos (como relatórios vitais originais em `.pdf`) em **Dados Prontos para IA** (AI-Ready Data).

---
> **Nota de Origem:** Este projeto nasceu e evoluiu como um experimento e caso de teste no âmbito do **IPAM** e da rede **MapBiomas**. O objetivo inicial foi criar uma solução ágil e de baixo custo para tornar grandes relatórios e documentos científicos (como o Relatório Anual do Fogo e Desmatamento) interativos e acessíveis à comunidade pública utilizando Inteligência Artificial (RAG). Posteriormente, sua arquitetura foi generalizada para a comunidade de Código Aberto.
---

Seja você um pesquisador, um analista de dados ou um desenvolvedor focado em RAG, o **Vector Hub Factory** automatiza a extração, o processamento semântico (chunking) e a vetorização (embeddings) dos seus documentos, ao mesmo tempo que levanta interfaces elegantes para acesso imediato.

---

## 🌟 O Que Essa Repositório Oferece?

1. **Fábricas Abertas (`/factory`):** Scripts modulares e padronizados para processamento. Se um documento não estiver processado, o "Orquestrador" detecta e vetoriza tudo automaticamente.
2. **Saídas de Dados Agnósticas:** Seu PDF entra; um banco vetorial (`faiss.index`) e seus metadados de chunking saem. 100% interoperável com qualquer pipeline de Machine Learning fora dessa aplicação.
3. **Vitrine e Chatbots Imediatos (`/ui`):** Suba o servidor e ganhe de brinde um Hub estático de distribuição de dados e três variações de chatbots em RAG (Multi-documentos, Cross-Search e Bots Específicos).
4. **Fácil Customização (`config.py`):** Mude cores, modifique logomarcas, altere prompts e crie relatórios apenas editando um simples arquivo de metadados global.

---

## 🚀 Como Começar? Iniciando o Servidor

Se os dados e índices já estiverem construídos, para levantar as páginas do Hub de distribuição e as aplicações Chatbot de uma vez, basta iniciar o ambiente virtual e rodar o servidor unificado FastAPI:

```bash
# 1. Ative seu ambiente virtual 
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/Mac

# 2. Inicie tudo pelo script organizador
.\start_all.bat
```

Seu Hub já estará online em `http://localhost:8000/`. A partir dele, você poderá navegar por:
- `/` ➔ Vitrine Estática de Distribuição
- `/multi` ➔ Chatbot RAG Multi-Relatório
- `/cross` ➔ Chatbot RAG de Busca Transversal Global
- `/chatbot-{nome}` ➔ O Chat próprio de um determinado documento

---

## 🌐 Hospedagem e Acesso Online

Este repositório foi construído com arquitetura Serverless-Ready.

### 1. Criar a sua API no Render (Backend)
Como a aplicação utiliza scripts Python robustos para inteligência artificial, precisamos de um pequeno servidor rodando gratuitamente na nuvem.
1. Crie uma conta no [Render](https://render.com).
2. Clique em **"New +"** e depois em **"Web Service"**.
3. Conecte sua conta do GitHub e selecione o seu fork ou clone do repositório `vector-hub-factory`.
4. Mantenha as configurações sugeridas, ou use caso ele peça manualmente:
   - **Language:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
5. Em **Environment Variables**, adicione sua chave de inteligência artificial provida pelo Google (ex: `GOOGLE_API_KEY`).
6. Clique em **Create Web Service**. Ele vai gerar o link do seu Backend (ex: `https://meu-servidor.onrender.com`). Guarde-o.

### 2. Configurar Interfaces e Hospedar o Hub (GitHub Pages)
Agora que sua API está funcional, basta dizermos para a Vitrine consumir as informações através dela e ligar as páginas gratuitas!
1. Vá no arquivo `ui/assets/config.js` no seu repositório.
2. Altere o valor de `API_URL` e cole com o seu link que o Render acabou de te fornecer. (Faça o push/commit dessa alteração).
3. Agora no GitHub, acesse a página do seu repositório > **Settings** > **Pages** (no menu lateral de opções).
4. Na seção **Build and deployment**, no campo *Source*, escolha a opção **GitHub Actions**.
5. O GitHub Actions vai compilar sua Vitrine. Em instantes, seu projeto será ativado no link padrão do GitHub Pages (ex: `https://<seu-usuario>.github.io/vector-hub-factory/`).

Pronto! Acesse o link que o GitHub Gerou para você. Toda vez que você mandar arquivos novos pro GitHub, ele publicará automaticamente as atualizações da interface visual e a API responderá com seus Chatbots e Arquivos.

---

## 🔨 Como Funciona a "Fábrica"? (Adicionando seus PDFs)

Não queremos perder horas quebrando cabeças com OCRs complexos e chunks errados. O fluxo "Padrão Prata" da fábrica foi feito para você focar no conteúdo.

Para adicionar um **Novo Documento**:

1. **Crie o Espaço do Documento:** Crie uma pasta dentro de `docs/` (ex: `docs/inovacao/`).
2. **Coloque seu PDF original lá:** `docs/inovacao/meu-relatorio.pdf`.
3. **Registre a nova "máquina"** no dicionário de metadados do `config.py`.
4. **Feche e deixe a Máquina Trabalhar:** 

Rode o orquestrador mágico na sua linha de comando:

```bash
python factory/00_run_all.py
```

O Orquestrador detectará os documentos faltantes, criará blocos (chunks), conversará com a inteligência artificial para injetar matrizes vetorizadas complexas e salvará seu PDF da obsolescência da ciência fechada os disponibilizando na pasta `/data/` interna do seu documento e automaticamente no seu Hub.

---

## 📂 Visão Rápida Arquitetural

```text
├── .agents/          # O 'Cérebro' do repositório (skills, tarefas e regras IA).
├── docs/             # Onde a mágica ocorre (Lugar dos seus PDFs e dados gerados).
├── factory/          # Os algoritmos gnósticos divididos da Máquina V.H.F.
├── src/              # O servidor RAG e roteamento da FastAPI principal (O Motor).
├── ui/               # Módulos Frontend HTML hiper estéticos que você navega e joga dados.
├── public/           # A Vitrine Estática final preparada pro GitHub Pages.
├── config.py         # 🎛️ O seu Painel de Comando Metadados. Tudo começa aqui.
└── start_all.bat     # O botão de START pra quando quiser apenas visualizar sua fábrica rodando.
```

## 🤝 Quer Estender as Funcionalidades?

Toda vez que uma Inteligência Artificial auxiliar trabalhar com você neste projeto, ela fará um check-up nos arquivos dentro de `.agents/skills/`. Esse diretório é inviolável. Se você deseja forçar a inteligência a sempre utilizar um layout *"Y"* para seus bots, ou testar modelos através do estilo *"Z"*, basta injetar uma "Skill" (Um manifesto Markdown lá dentro) baseando-se no `html_app_factory`. Ela seguirá esse plano milimetricamente a qualquer nova expansão do Web App.

---
*Construído com Ciência Aberta, IAs Auxiliares e Arquitetura Limpa.*