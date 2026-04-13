// Gerenciador de Guias Dinâmicas do Canvas
class TabManager {
    constructor(containerId, contentClass = 'tab-content') {
        console.log('[TabManager] Constructor started, container:', containerId);
        this.container = document.getElementById(containerId);
        this.contentClass = contentClass;
        this.tabs = {};
        this.activeTabId = null;
        
        console.log('[TabManager] Container element:', this.container);

        // Injetar a estrutura HTML básica no contêiner
        this.container.innerHTML = `
            <div class="canvas-tab-bar" id="${containerId}-tab-bar"></div>
            <div class="${this.contentClass} pdf-mode" id="${containerId}-content-area"></div>
        `;
        
        this.tabBar = document.getElementById(`${containerId}-tab-bar`);
        this.contentArea = document.getElementById(`${containerId}-content-area`);
        
        // Suporte a ?tab= na URL
        this.initFromURL();
    }
    
    initFromURL() {
        const params = new URLSearchParams(window.location.search);
        const tab = params.get('tab');
        if (tab) {
            this._pendingTab = tab;
        }
    }
    
    activatePendingTab() {
        if (this._pendingTab && this.tabs[this._pendingTab]) {
            this.activateTab(this._pendingTab);
            this._pendingTab = null;
        }
    }

    addTab(id, title, isClosable, contentHTML, icon = '📄') {
        if (this.tabs[id]) return this.activateTab(id);

        const tabEl = document.createElement('div');
        tabEl.className = 'canvas-tab';
        tabEl.dataset.tabId = id;
        tabEl.innerHTML = `<span>${icon} ${title}</span>`;
        if (isClosable) {
            const closeBtn = document.createElement('span');
            closeBtn.className = 'tab-close';
            closeBtn.innerHTML = '×';
            closeBtn.onclick = (e) => {
                e.stopPropagation();
                this.closeTab(id);
            };
            tabEl.appendChild(closeBtn);
        }
        tabEl.onclick = () => this.activateTab(id);
        
        const contentEl = document.createElement('div');
        contentEl.className = 'tab-panel';
        contentEl.dataset.tabId = id;
        contentEl.style.display = 'none';
        contentEl.style.width = '100%';
        contentEl.style.height = '100%';
        contentEl.innerHTML = contentHTML;

        this.tabBar.appendChild(tabEl);
        this.contentArea.appendChild(contentEl);

        this.tabs[id] = { tabEl, contentEl };
        
        this.activateTab(id);
    }

    activateTab(id, updateURL = true) {
        if (!this.tabs[id]) return;
        
        // Atualizar URL sem recarregar a página
        if (updateURL && typeof window !== 'undefined') {
            const url = new URL(window.location.href);
            url.searchParams.set('tab', id);
            window.history.replaceState({}, '', url.toString());
        }
        
        // Desativar todas
        Object.values(this.tabs).forEach(t => {
            t.tabEl.classList.remove('active');
            t.tabEl.classList.remove('tab-flash');
            t.contentEl.style.display = 'none';
        });

        // Ativar selecionada
        this.tabs[id].tabEl.classList.add('active');
        this.tabs[id].tabEl.classList.add('tab-flash'); // Visual highlight
        setTimeout(() => this.tabs[id].tabEl.classList.remove('tab-flash'), 1500);
        
        this.tabs[id].contentEl.style.display = 'block';
        this.activeTabId = id;
        
        // Ajustar fundo da área de conteúdo dependendo da aba
        if(id.includes('pdf') || id === 'raf' || id === 'rad') {
            this.contentArea.classList.add('pdf-mode');
        } else {
            this.contentArea.classList.remove('pdf-mode');
        }
    }

    closeTab(id) {
        if (!this.tabs[id]) return;
        this.tabs[id].tabEl.remove();
        this.tabs[id].contentEl.remove();
        delete this.tabs[id];

        if (this.activeTabId === id) {
            // Ativar a primeira aba disponível (idealmente o PDF)
            const remaining = Object.keys(this.tabs);
            if (remaining.length > 0) {
                this.activateTab(remaining[0]);
            }
        }
    }
}

window.TabManager = TabManager;
