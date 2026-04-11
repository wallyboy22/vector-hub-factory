# 🏭 Vector Hub Factory

Uma plataforma modular de Ciência Aberta para transformar documentos científicos estáticos (como relatórios vitais originais em `.pdf`) em **Dados Prontos para IA** (AI-Ready Data).

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

### 1. Frontend: Vitrine no GitHub Pages
Seu repositório já possui integração contínua (GitHub Actions) para publicar a interface automaticamente!
Para ativar e acessar a experiência online:
1. Vá na página do seu repositório no GitHub.
2. Acesse **Settings** (Configurações) > **Pages** (no menu lateral esquerdo).
3. Na seção **Build and deployment**, em *Source*, garanta que esteja selecionado **GitHub Actions**.
4. Em instantes, o GitHub vai compilar e sua vitrine estará disponível em: `https://<seu-usuario>.github.io/vector-hub-factory/`
*(Nota: Substitua `<seu-usuario>` por `wallyboy22`)*

### 2. Backend: A Inteligência e os PDFs
A vitrine no GitHub Pages é estática. Para que os chatbots respondam e os PDFs carreguem corretamente pra quem acessar aquele link público, o motor (`src/api.py`) precisa estar rodando.
- **Opção A (Gratuita na Nuvem):** Conectar este repositório no serviço [Render](https://render.com). O arquivo `render.yaml` já está configurado. O Render vai gerar uma URL para a sua API (ex: `https://seu-app.onrender.com`).
- Após ter essa URL, você só precisa ir no arquivo `ui/assets/config.js` e atualizar a variável `API_URL` com ela.
- E pronto! A Vitrine no seu GitHub Pages consumirá a Inteligência em tempo real pela Nuvem!

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