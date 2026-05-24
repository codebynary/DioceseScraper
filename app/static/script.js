/**
 * Diocese Scraper - Client-side Interaction JavaScript
 * Author: Antigravity AI
 */

document.addEventListener('DOMContentLoaded', () => {
    // Helper functions for structured parish fields fallback
    function getFlatClero(p) {
        if (!p) return '';
        if (p.clero_original && typeof p.clero_original === 'string') {
            return p.clero_original;
        }
        if (typeof p.clero === 'string') {
            return p.clero;
        }
        if (Array.isArray(p.clero)) {
            return p.clero.map(m => m.texto_original || [m.titulo, m.nome, m.cargo].filter(Boolean).join(' ')).filter(Boolean).join('\n');
        }
        return '';
    }

    function getFlatEndereco(p) {
        if (!p) return '';
        if (p.endereco_original && typeof p.endereco_original === 'string') {
            return p.endereco_original;
        }
        if (typeof p.endereco === 'string') {
            return p.endereco;
        }
        if (p.endereco && typeof p.endereco === 'object') {
            return p.endereco.original || '';
        }
        return '';
    }

    function getFlatSecretaria(p) {
        if (!p) return '';
        if (p.funcionamento_secretaria_original && typeof p.funcionamento_secretaria_original === 'string') {
            return p.funcionamento_secretaria_original;
        }
        if (typeof p.funcionamento_secretaria === 'string') {
            return p.funcionamento_secretaria;
        }
        if (p.funcionamento_secretaria && typeof p.funcionamento_secretaria === 'object') {
            return p.funcionamento_secretaria.texto_original || '';
        }
        return '';
    }

    function getFlatMissas(p) {
        if (!p) return '';
        if (typeof p.horarios_missa_texto === 'string') {
            return p.horarios_missa_texto;
        }
        if (p.horarios_missa_texto_original && typeof p.horarios_missa_texto_original === 'string') {
            return p.horarios_missa_texto_original;
        }
        if (Array.isArray(p.horarios_missa)) {
            return p.horarios_missa.map(h => h.texto_original || h.observacoes || '').filter(Boolean).join('\n');
        }
        return '';
    }

    // State management
    let activeDioceseId = null;
    let activeDioceseName = null;
    let dioceseList = [];
    let currentConfigData = null; // Stored from AI analysis before confirming
    let sseSource = null;

    // DOM Elements
    const btnApiSettings = document.getElementById('btn-api-settings');
    const apiKeyBanner = document.getElementById('api-key-banner');
    const btnConfigNow = document.getElementById('btn-config-now');
    
    // Modals
    const modalApiKey = document.getElementById('modal-api-key');
    const modalNewDiocese = document.getElementById('modal-new-diocese');
    const modalCloses = document.querySelectorAll('.modal-close, .modal-close-btn');
    
    // API Key Modal elements
    const inputApiKey = document.getElementById('input-api-key');
    const btnToggleKeyVisibility = document.getElementById('btn-toggle-key-visibility');
    const btnSaveApiKey = document.getElementById('btn-save-api-key');
    const apiKeyFeedback = document.getElementById('api-key-feedback');

    // New Diocese Modal / AI elements
    const btnNewScrape = document.getElementById('btn-new-scrape');
    const btnRunAnalysis = document.getElementById('btn-run-analysis');
    const btnSaveConfirm = document.getElementById('btn-save-confirm');
    const btnAnalyzeBack = document.getElementById('btn-analyze-back');
    const btnAnalyzeCancel = document.getElementById('btn-analyze-cancel');
    
    const analyzeStepInput = document.getElementById('analyze-step-input');
    const analyzeStepLoading = document.getElementById('analyze-step-loading');
    const analyzeStepResult = document.getElementById('analyze-step-result');
    const inputDioceseName = document.getElementById('input-diocese-name');
    const inputDioceseUrl = document.getElementById('input-diocese-url');
    const analyzeFeedback = document.getElementById('analyze-feedback');
    
    // Test Parish Preview Elements
    const previewImage = document.getElementById('preview-image');
    const previewNome = document.getElementById('preview-nome');
    const previewUrl = document.getElementById('preview-url');
    const previewSetor = document.getElementById('preview-setor');
    const previewClero = document.getElementById('preview-clero');
    const previewTelefone = document.getElementById('preview-telefone');
    const previewEmail = document.getElementById('preview-email');
    const previewSecretaria = document.getElementById('preview-secretaria');
    const previewEndereco = document.getElementById('preview-endereco');
    const previewRedes = document.getElementById('preview-redes');
    const previewMissas = document.getElementById('preview-missas');
    const configJsonTextarea = document.getElementById('config-json-textarea');

    // Sidebar & Viewers
    const diocesesCount = document.getElementById('dioceses-count');
    const diocesesListContainer = document.getElementById('dioceses-list');
    const emptyState = document.getElementById('empty-state');
    
    // Scraper Progress elements
    const scrapeProgressPanel = document.getElementById('scrape-progress-panel');
    const progressDioceseName = document.getElementById('progress-diocese-name');
    const terminalBody = document.getElementById('terminal-body');
    const btnClearTerminal = document.getElementById('btn-clear-terminal');
    
    // UI Elements - Viewer Panel
    const dataViewerPanel = document.getElementById('data-viewer-panel');
    const viewerDioceseName = document.getElementById('viewer-diocese-name');
    const viewerStats = document.getElementById('viewer-stats');
    const btnReMap = document.getElementById('btn-re-map');
    const btnReScrape = document.getElementById('btn-re-scrape');
    const btnAppendSource = document.getElementById('btn-append-source');
    const btnExportJson = document.getElementById('btn-export-json');
    const btnDeleteDiocese = document.getElementById('btn-delete-diocese');
    const searchParishes = document.getElementById('search-parishes');
    const parishesTableBody = document.getElementById('parishes-table-body');

    // Append Source Modal elements
    const modalAppendSource = document.getElementById('modal-append-source');
    const inputAppendUrl = document.getElementById('input-append-url');
    const appendFeedback = document.getElementById('append-feedback');
    const btnStartAppend = document.getElementById('btn-start-append');
    
    // Import MD Elements
    const inputMdFiles = document.getElementById('input-md-files');
    const btnUploadMd = document.getElementById('btn-upload-md');
    const uploadFeedback = document.getElementById('upload-feedback');

    let parishDataCached = []; // For local search/filtering

    // Initial Loading
    checkApiKeyStatus();
    loadDiocesesList();

    // ==========================================
    // API KEY MANAGEMENT
    // ==========================================

    function checkApiKeyStatus() {
        fetch('/api/api-key')
            .then(res => res.json())
            .then(data => {
                if (data.key_exists) {
                    apiKeyBanner.classList.add('hidden');
                    btnApiSettings.innerHTML = '<i class="fa-solid fa-key"></i> Chave Configurada';
                    btnApiSettings.classList.remove('btn-secondary');
                    btnApiSettings.classList.add('btn-success');
                } else {
                    apiKeyBanner.classList.remove('hidden');
                    btnApiSettings.innerHTML = '<i class="fa-solid fa-key"></i> Chave Gemini';
                    btnApiSettings.classList.add('btn-secondary');
                    btnApiSettings.classList.remove('btn-success');
                }
            })
            .catch(err => console.error('Erro ao verificar chave API:', err));
    }

    btnApiSettings.addEventListener('click', () => openModal(modalApiKey));
    btnConfigNow.addEventListener('click', () => openModal(modalApiKey));

    // Password visibility toggle
    btnToggleKeyVisibility.addEventListener('click', () => {
        const type = inputApiKey.getAttribute('type') === 'password' ? 'text' : 'password';
        inputApiKey.setAttribute('type', type);
        btnToggleKeyVisibility.innerHTML = type === 'password' ? '<i class="fa-solid fa-eye"></i>' : '<i class="fa-solid fa-eye-slash"></i>';
    });

    btnSaveApiKey.addEventListener('click', () => {
        const apiKey = inputApiKey.value.trim();
        if (!apiKey) {
            showFeedback(apiKeyFeedback, 'Por favor, insira a chave de API.', 'error');
            return;
        }

        btnSaveApiKey.disabled = true;
        btnSaveApiKey.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Validando...';
        showFeedback(apiKeyFeedback, null); // Clear

        fetch('/api/api-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        })
        .then(async res => {
            const data = await res.json();
            if (res.ok) {
                showFeedback(apiKeyFeedback, data.message, 'success');
                setTimeout(() => {
                    closeModal(modalApiKey);
                    checkApiKeyStatus();
                    inputApiKey.value = '';
                    showFeedback(apiKeyFeedback, null);
                }, 1500);
            } else {
                showFeedback(apiKeyFeedback, data.message || 'Falha ao validar a chave.', 'error');
            }
        })
        .catch(err => {
            showFeedback(apiKeyFeedback, 'Erro na requisição. Verifique sua conexão.', 'error');
            console.error(err);
        })
        .finally(() => {
            btnSaveApiKey.disabled = false;
            btnSaveApiKey.innerHTML = 'Salvar e Validar';
        });
    });

    // ==========================================
    // DIOCESES LIST / SIDEBAR
    // ==========================================

    function loadDiocesesList() {
        fetch('/api/dioceses')
            .then(res => res.json())
            .then(data => {
                dioceseList = data;
                diocesesCount.textContent = data.length;
                renderDiocesesList();
            })
            .catch(err => {
                console.error('Erro ao carregar lista de dioceses:', err);
                diocesesListContainer.innerHTML = `
                    <div class="list-empty error">
                        <i class="fa-solid fa-circle-exclamation text-danger"></i> Erro ao carregar dioceses.
                    </div>
                `;
            });
    }

    function renderDiocesesList() {
        if (dioceseList.length === 0) {
            diocesesListContainer.innerHTML = `
                <div class="list-empty">
                    <i class="fa-solid fa-church"></i> Nenhuma diocese configurada.
                </div>
            `;
            return;
        }

        diocesesListContainer.innerHTML = '';
        dioceseList.forEach(diocese => {
            const item = document.createElement('div');
            item.className = `diocese-item ${activeDioceseId === diocese.id ? 'active' : ''}`;
            item.dataset.id = diocese.id;
            item.dataset.nome = diocese.nome;

            const total = diocese.total_paroquias || 0;
            const paginationTypeLabel = getPaginationTypeLabel(diocese.config.paginacao.tipo);

            item.innerHTML = `
                <div class="diocese-item-header">
                    <span class="diocese-item-name">${diocese.nome}</span>
                    <span class="diocese-item-badge">${paginationTypeLabel}</span>
                </div>
                <span class="diocese-item-url">${diocese.url_base}</span>
                <div class="diocese-item-footer">
                    <span class="diocese-item-stats">
                        <i class="fa-solid fa-circle-info"></i> ${total} paróquia(s) salva(s)
                    </span>
                    <i class="fa-solid fa-chevron-right text-muted" style="font-size: 0.75rem;"></i>
                </div>
            `;

            item.addEventListener('click', () => {
                selectDiocese(diocese.id, diocese.nome);
            });

            diocesesListContainer.appendChild(item);
        });
    }

    function getPaginationTypeLabel(type) {
        switch (type) {
            case 'url_page': return 'Paginação URL';
            case 'link_next': return 'Próxima Pág.';
            default: return 'Pág. Única';
        }
    }

    function selectDiocese(id, nome) {
        activeDioceseId = id;
        activeDioceseName = nome;
        
        // Update selection UI
        document.querySelectorAll('.diocese-item').forEach(el => {
            if (el.dataset.id === id) el.classList.add('active');
            else el.classList.remove('active');
        });

        emptyState.classList.add('hidden');
        scrapeProgressPanel.classList.add('hidden');
        dataViewerPanel.classList.remove('hidden');

        viewerDioceseName.textContent = nome;
        viewerStats.textContent = 'Carregando paróquias...';
        parishesTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 1.5rem;"></i> Carregando dados...
                </td>
            </tr>
        `;

        fetch(`/api/data/${id}`)
            .then(res => res.json())
            .then(data => {
                parishDataCached = data;
                viewerStats.textContent = `${data.length} paróquia(s) catalogada(s)`;
                renderParishTable(data);
            })
            .catch(err => {
                console.error(err);
                parishesTableBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-4 text-danger">
                            Erro ao carregar os dados desta diocese. Certifique-se de que a extração foi executada.
                        </td>
                    </tr>
                `;
            });
    }

    // ==========================================
    // PARISH DATA TABLE & SEARCH
    // ==========================================

    function renderParishTable(data) {
        if (!data || data.length === 0) {
            parishesTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4">
                        Nenhum registro encontrado. Rode o scraper para extrair dados.
                    </td>
                </tr>
            `;
            return;
        }

        parishesTableBody.innerHTML = '';
        data.forEach(p => {
            const tr = document.createElement('tr');
            
            // Set row status classes
            if (p.status === 'removido') {
                tr.classList.add('row-removed');
            }
            
            // Status badges
            let statusBadgesHtml = '';
            if (p.status === 'removido') {
                statusBadgesHtml += `<span class="status-badge status-badge-removido"><i class="fa-solid fa-trash-can"></i> Removido</span>`;
            } else if (p.status === 'novo') {
                statusBadgesHtml += `<span class="status-badge status-badge-novo"><i class="fa-solid fa-circle-plus"></i> Novo</span>`;
            }
            if (p.curado) {
                statusBadgesHtml += `<span class="status-badge status-badge-curado"><i class="fa-solid fa-circle-check"></i> Curado</span>`;
            }
            
            // Thumbnail image or default icon
            const thumb = p.imagem_thumbnail 
                ? `<img src="${p.imagem_thumbnail}" alt="${p.nome}" onerror="this.outerHTML='<i class=fa-solid fa-church></i>'">`
                : `<i class="fa-solid fa-church"></i>`;
                
            // Clergy
            let clergyHtml = '';
            const cleroFlat = getFlatClero(p);
            if (cleroFlat) {
                const members = cleroFlat.split('\n').filter(Boolean);
                members.forEach(m => {
                    clergyHtml += `<span class="clergy-member">${m}</span>`;
                });
            } else {
                clergyHtml = '<span class="text-dark">-</span>';
            }

            // Contact info
            let contactsHtml = '';
            if (p.telefone) {
                contactsHtml += `<div class="contact-item"><i class="fa-solid fa-phone"></i> <span>${p.telefone}</span></div>`;
            }
            if (p.email) {
                contactsHtml += `<div class="contact-item"><i class="fa-solid fa-envelope"></i> <span>${p.email}</span></div>`;
            }
            const secretariaFlat = getFlatSecretaria(p);
            if (secretariaFlat) {
                contactsHtml += `<div class="contact-item" title="${secretariaFlat}"><i class="fa-solid fa-clock"></i> <span class="address-text text-truncate">${secretariaFlat}</span></div>`;
            }
            if (!contactsHtml) contactsHtml = '<span class="text-dark">-</span>';

            // Address
            let addressHtml = '';
            const enderecoFlat = getFlatEndereco(p);
            if (enderecoFlat) {
                addressHtml += `<span class="address-text" title="${enderecoFlat}">${enderecoFlat}</span>`;
            } else {
                addressHtml = '<span class="text-dark">-</span>';
            }

            // Social Media
            let socialHtml = '';
            let hasSocial = false;
            if (p.redes_sociais && Object.keys(p.redes_sociais).length > 0) {
                Object.entries(p.redes_sociais).forEach(([net, link]) => {
                    const url = link && typeof link === 'object' ? (link.url || '') : (link || '');
                    if (!url) return;
                    
                    hasSocial = true;
                    let icon = 'fa-solid fa-link';
                    if (net === 'facebook') icon = 'fa-brands fa-facebook-f';
                    else if (net === 'instagram') icon = 'fa-brands fa-instagram';
                    else if (net === 'youtube') icon = 'fa-brands fa-youtube';
                    else if (net === 'whatsapp') icon = 'fa-brands fa-whatsapp';
                    
                    socialHtml += `<a href="${url}" target="_blank" class="social-pill ${net}"><i class="${icon}"></i></a>`;
                });
            }
            if (!hasSocial) {
                socialHtml = '<span class="text-dark">-</span>';
            }

            // Sector / Setor
            const sectorBadge = p.setor 
                ? `<span class="sector-badge">${p.setor}</span>`
                : '<span class="text-dark">-</span>';

            tr.innerHTML = `
                <td>
                    <div class="parish-main-cell">
                        <div class="parish-avatar">${thumb}</div>
                        <div>
                            <div class="parish-name-row">
                                <a href="${p.url}" target="_blank" class="parish-name-link">${p.nome}</a>
                                ${statusBadgesHtml}
                            </div>
                            <span class="parish-external-link">${addressHtml}</span>
                        </div>
                    </div>
                </td>
                <td>${sectorBadge}</td>
                <td>${clergyHtml}</td>
                <td>${contactsHtml}</td>
                <td>${socialHtml}</td>
            `;

            parishesTableBody.appendChild(tr);
        });

        // Marca rows como clicáveis (o click handler fica no delegation abaixo)
        parishesTableBody.querySelectorAll('tr').forEach(tr => tr.classList.add('clickable-row'));
    }

    // Event delegation: único listener no tbody, resolve índice dinamicamente
    parishesTableBody.addEventListener('click', (e) => {
        if (e.target.closest('a')) return; // ignora cliques em links/redes sociais
        const tr = e.target.closest('tr');
        if (!tr) return;
        const rows = Array.from(parishesTableBody.querySelectorAll('tr'));
        const rowIdx = rows.indexOf(tr);
        if (rowIdx === -1) return;
        // Acha a paróquia correspondente na lista filtrada atual
        const visibleData = parishDataCached.filter(p => {
            const query = searchParishes.value.toLowerCase().trim();
            if (!query) return true;
            return [
                p.nome, p.setor, getFlatClero(p), p.email, p.telefone, getFlatEndereco(p)
            ].some(f => f && typeof f === 'string' && f.toLowerCase().includes(query));
        });
        const parish = visibleData[rowIdx];
        if (!parish) return;
        const realIndex = parishDataCached.indexOf(parish);
        openParishModal(realIndex !== -1 ? realIndex : rowIdx);
    });


    // Filter parishes in search bar
    searchParishes.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            renderParishTable(parishDataCached);
            return;
        }

        const filtered = parishDataCached.filter(p => {
            const name = (p.nome || '').toLowerCase();
            const sector = (p.setor || '').toLowerCase();
            const clero = getFlatClero(p).toLowerCase();
            const email = (p.email || '').toLowerCase();
            const tel = (p.telefone || '').toLowerCase();
            const addr = getFlatEndereco(p).toLowerCase();
            
            return name.includes(query) || 
                   sector.includes(query) || 
                   clero.includes(query) || 
                   email.includes(query) || 
                   tel.includes(query) || 
                   addr.includes(query);
        });

        renderParishTable(filtered);
    });

    // ==========================================
    // AI LAYOUT ANALYSIS (ADD NEW SITE)
    // ==========================================

    btnNewScrape.addEventListener('click', () => {
        // Reset analysis wizard
        inputDioceseName.value = '';
        inputDioceseUrl.value = '';
        showFeedback(analyzeFeedback, null);
        
        analyzeStepInput.classList.remove('hidden');
        analyzeStepLoading.classList.add('hidden');
        analyzeStepResult.classList.add('hidden');
        
        btnRunAnalysis.classList.remove('hidden');
        btnSaveConfirm.classList.add('hidden');
        btnAnalyzeBack.classList.add('hidden');
        btnAnalyzeCancel.classList.remove('hidden');
        
        openModal(modalNewDiocese);
    });

    btnRunAnalysis.addEventListener('click', () => {
        const name = inputDioceseName.value.trim();
        const url = inputDioceseUrl.value.trim();

        if (!name || !url) {
            showFeedback(analyzeFeedback, 'Nome e URL são campos obrigatórios.', 'error');
            return;
        }

        // Check if URL is valid
        try {
            new URL(url);
        } catch (_) {
            showFeedback(analyzeFeedback, 'Insira uma URL de listagem válida.', 'error');
            return;
        }

        showFeedback(analyzeFeedback, null);
        
        // Go to Loading state
        analyzeStepInput.classList.add('hidden');
        analyzeStepLoading.classList.remove('hidden');
        btnRunAnalysis.classList.add('hidden');
        btnAnalyzeCancel.classList.add('hidden');

        fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: name, url_base: url })
        })
        .then(async res => {
            const data = await res.ok ? await res.json() : null;
            if (data && data.success) {
                // Store globally to use on confirm
                currentConfigData = data.config;
                
                // Populating preview UI
                const p = data.test_parish || {};
                
                previewNome.textContent = p.nome || 'Paróquia não mapeada';
                previewUrl.textContent = p.url || '';
                previewSetor.textContent = p.setor || '-';
                previewClero.textContent = getFlatClero(p) || '-';
                previewTelefone.textContent = p.telefone || '-';
                previewEmail.textContent = p.email || '-';
                previewSecretaria.textContent = getFlatSecretaria(p) || '-';
                previewEndereco.textContent = getFlatEndereco(p) || '-';
                previewMissas.textContent = getFlatMissas(p) || '-';
                
                // Redes
                let socialText = '';
                if (p.redes_sociais && Object.keys(p.redes_sociais).length > 0) {
                    const activeKeys = Object.entries(p.redes_sociais)
                        .filter(([_, link]) => {
                            const url = link && typeof link === 'object' ? (link.url || '') : (link || '');
                            return !!url;
                        })
                        .map(([net, _]) => net);
                    socialText = activeKeys.length > 0 ? activeKeys.join(', ') : 'Nenhuma';
                } else {
                    socialText = 'Nenhuma';
                }
                previewRedes.textContent = socialText;

                // Image thumbnail
                if (p.imagem_thumbnail) {
                    previewImage.innerHTML = `<img src="${p.imagem_thumbnail}" alt="Thumbnail" onerror="this.outerHTML='<i class=fa-solid fa-church></i>'">`;
                } else {
                    previewImage.innerHTML = `<i class="fa-solid fa-church"></i>`;
                }

                // Config textarea representation
                configJsonTextarea.value = JSON.stringify(data.config, null, 2);

                // Show step 3 (Result Review)
                analyzeStepLoading.classList.add('hidden');
                analyzeStepResult.classList.remove('hidden');
                btnSaveConfirm.classList.remove('hidden');
                btnAnalyzeBack.classList.remove('hidden');
                btnAnalyzeCancel.classList.remove('hidden');
            } else {
                // Get error message if possible
                let msg = 'Ocorreu um erro ao rodar a análise por IA.';
                try {
                    const errObj = await res.json();
                    msg = errObj.message || msg;
                } catch(_) {}
                
                // Go back to input with error
                analyzeStepLoading.classList.add('hidden');
                analyzeStepInput.classList.remove('hidden');
                btnRunAnalysis.classList.remove('hidden');
                btnAnalyzeCancel.classList.remove('hidden');
                showFeedback(analyzeFeedback, msg, 'error');
            }
        })
        .catch(err => {
            console.error(err);
            analyzeStepLoading.classList.add('hidden');
            analyzeStepInput.classList.remove('hidden');
            btnRunAnalysis.classList.remove('hidden');
            btnAnalyzeCancel.classList.remove('hidden');
            showFeedback(analyzeFeedback, 'Erro de rede ao conectar com o backend. Verifique o console.', 'error');
        });
    });

    btnAnalyzeBack.addEventListener('click', () => {
        // Go back from step 3 to step 1
        analyzeStepResult.classList.add('hidden');
        analyzeStepInput.classList.remove('hidden');
        btnRunAnalysis.classList.remove('hidden');
        btnSaveConfirm.classList.add('hidden');
        btnAnalyzeBack.classList.add('hidden');
    });

    // Save and run scraper immediately on confirmed config
    btnSaveConfirm.addEventListener('click', () => {
        // Validate textarea manual adjustments
        let finalConfig = null;
        try {
            finalConfig = JSON.parse(configJsonTextarea.value);
        } catch (e) {
            alert('A configuração editada não é um JSON válido. Corrija o formato antes de prosseguir.');
            return;
        }

        btnSaveConfirm.disabled = true;
        btnSaveConfirm.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Salvando...';

        fetch('/api/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: finalConfig })
        })
        .then(async res => {
            const data = await res.json();
            if (res.ok) {
                closeModal(modalNewDiocese);
                // Trigger the scrape stream directly for this new diocese
                startScrapingProcess(data.config_id, finalConfig.nome);
            } else {
                alert(data.message || 'Erro ao salvar a diocese.');
                btnSaveConfirm.disabled = false;
                btnSaveConfirm.innerHTML = 'Confirmar e Iniciar Raspagem';
            }
        })
        .catch(err => {
            console.error(err);
            alert('Erro de rede ao salvar a configuração.');
            btnSaveConfirm.disabled = false;
            btnSaveConfirm.innerHTML = 'Confirmar e Iniciar Raspagem';
        });
    });

    // ==========================================
    // SCRAPING EXECUTION ENGINE (SSE STREAM)
    // ==========================================

    function startScrapingProcess(configId, name) {
        activeDioceseId = configId;
        activeDioceseName = name;

        // UI state toggle
        emptyState.classList.add('hidden');
        dataViewerPanel.classList.add('hidden');
        scrapeProgressPanel.classList.remove('hidden');

        progressDioceseName.textContent = `Raspando: ${name}`;
        terminalBody.innerHTML = '';
        appendLog('Solicitando conexão para início da raspagem...');

        // Close existing event source if any
        if (sseSource) {
            sseSource.close();
        }

        // Start SSE stream
        sseSource = new EventSource(`/api/scrape/stream/${configId}`);

        sseSource.onmessage = (event) => {
            const logLine = event.data;
            appendLog(logLine);

            // Check if log contains success or completion flags
            if (logLine.includes('SUCESSO:') || logLine.includes('ERRO:') || logLine.includes('Cancelando extração')) {
                sseSource.close();
                appendLog('\n--- FIM DO PROCESSO ---');
                
                // Reload list of dioceses to show updated parish counts
                loadDiocesesList();
                
                // Show view table button/action or navigate automatically after 3 seconds
                setTimeout(() => {
                    selectDiocese(configId, name);
                }, 3000);
            }
        };

        sseSource.onerror = (err) => {
            console.error('SSE Error:', err);
            sseSource.close();
            loadDiocesesList();

            // O scrape pode ter terminado com sucesso mesmo sem o sinal chegar.
            // Tenta carregar os dados após 2s para verificar.
            appendLog('\n[SISTEMA] Conexão encerrada. Verificando se dados foram salvos...');
            setTimeout(() => {
                fetch(`/api/dioceses`)
                    .then(r => r.json())
                    .then(list => {
                        const diocese = list.find(d => d.id === configId);
                        if (diocese && diocese.total_paroquias > 0) {
                            appendLog(`[SISTEMA] Dados encontrados! ${diocese.total_paroquias} paróquia(s) salva(s). Carregando...`);
                            setTimeout(() => selectDiocese(configId, name), 1500);
                        } else {
                            appendLog('[SISTEMA ERROR] Conexão com o servidor de streaming foi encerrada antes de salvar dados.');
                        }
                    })
                    .catch(() => {
                        appendLog('[SISTEMA ERROR] Não foi possível verificar os dados salvos.');
                    });
            }, 2000);
        };
    }

    btnReScrape.addEventListener('click', () => {
        if (activeDioceseId && activeDioceseName) {
            if (confirm(`Deseja rodar novamente a raspagem para "${activeDioceseName}"? Os dados novos serão mesclados com os existentes, preservando suas curadorias.`)) {
                startScrapingProcess(activeDioceseId, activeDioceseName);
            }
        }
    });

    // ==========================================
    // ADICIONAR FONTES (APPEND SOURCE)
    // ==========================================

    btnAppendSource.addEventListener('click', () => {
        if (!activeDioceseId) return;
        inputAppendUrl.value = '';
        showFeedback(appendFeedback, null);
        openModal(modalAppendSource);
    });

    btnStartAppend.addEventListener('click', () => {
        const url = inputAppendUrl.value.trim();
        if (!url) {
            showFeedback(appendFeedback, 'Por favor, insira uma URL válida.', 'error');
            return;
        }

        closeModal(modalAppendSource);

        // Show terminal panel and connect to SSE append stream
        dataViewerPanel.classList.add('hidden');
        emptyState.classList.add('hidden');
        scrapeProgressPanel.classList.remove('hidden');
        progressDioceseName.textContent = `Adicionando fontes: ${activeDioceseName}`;
        terminalBody.innerHTML = '';

        const encodedUrl = encodeURIComponent(url);
        const evtSource = new EventSource(`/api/scrape/stream-append/${activeDioceseId}?url_override=${encodedUrl}`);

        evtSource.onmessage = (event) => {
            const msg = event.data;
            appendLog(msg);
            if (msg.includes('[CONCLUÍDO]') || msg.includes('[ERRO]') || msg.includes('✅') || msg.includes('paróquias salvas')) {
                evtSource.close();
                setTimeout(() => {
                    scrapeProgressPanel.classList.add('hidden');
                    dataViewerPanel.classList.remove('hidden');
                    selectDiocese(activeDioceseId, activeDioceseName);
                    loadDiocesesList();
                }, 2000);
            }
        };

        evtSource.onerror = () => {
            evtSource.close();
            appendLog('[SISTEMA] Conexão encerrada.');
            setTimeout(() => {
                scrapeProgressPanel.classList.add('hidden');
                dataViewerPanel.classList.remove('hidden');
                selectDiocese(activeDioceseId, activeDioceseName);
            }, 2000);
        };
    });


    btnReMap.addEventListener('click', () => {
        if (activeDioceseId && activeDioceseName) {
            const currentDiocese = dioceseList.find(d => d.id === activeDioceseId);
            if (currentDiocese) {
                inputDioceseName.value = currentDiocese.nome;
                inputDioceseUrl.value = currentDiocese.url_base;
                showFeedback(analyzeFeedback, null);
                
                analyzeStepInput.classList.remove('hidden');
                analyzeStepLoading.classList.add('hidden');
                analyzeStepResult.classList.add('hidden');
                
                btnRunAnalysis.classList.remove('hidden');
                btnSaveConfirm.classList.add('hidden');
                btnAnalyzeBack.classList.add('hidden');
                btnAnalyzeCancel.classList.remove('hidden');
                
                openModal(modalNewDiocese);
            }
        }
    });

    btnClearTerminal.addEventListener('click', () => {
        terminalBody.innerHTML = '';
    });

    // ==========================================
    // GENERAL MODAL HELPERS
    // ==========================================

    function openModal(modal) {
        modal.classList.add('open');
    }

    function closeModal(modal) {
        modal.classList.remove('open');
    }

    modalCloses.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) closeModal(modal);
        });
    });

    // Close modal if clicking background
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target);
        }
    });

    // Helper to display feedback text on forms
    function showFeedback(element, message, type = 'success') {
        if (!message) {
            element.style.display = 'none';
            element.textContent = '';
            element.className = 'feedback-msg';
            return;
        }
        element.textContent = message;
        element.className = `feedback-msg ${type}`;
        element.style.display = 'block';
    }

    // Helper to append log lines in the Console screen
    function appendLog(line) {
        const div = document.createElement('div');
        div.className = 'terminal-log-entry';
        
        // Syntax highlight some key log phrases
        if (line.includes('SUCESSO:')) {
            div.style.color = '#10b981';
            div.style.fontWeight = 'bold';
        } else if (line.includes('ERRO:')) {
            div.style.color = '#ef4444';
            div.style.fontWeight = 'bold';
        } else if (line.startsWith('===')) {
            div.style.color = '#8b5cf6';
            div.style.fontWeight = 'bold';
            div.style.marginTop = '10px';
        } else if (line.includes('Acessando página')) {
            div.style.color = '#60a5fa';
        } else if (line.includes('Extraindo detalhes de:')) {
            div.style.color = '#e2e8f0';
        }

        div.textContent = line;
        terminalBody.appendChild(div);
        
        // Scroll terminal to bottom
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    // ==========================================
    // PARISH CURATION MODAL
    // ==========================================

    let currentParishIndex = 0;
    const modalParishDetail = document.getElementById('modal-parish-detail');
    const btnDetailPrev = document.getElementById('btn-detail-prev');
    const btnDetailNext = document.getElementById('btn-detail-next');
    const btnSaveCuration = document.getElementById('btn-save-curation');
    const detailSaveFeedback = document.getElementById('detail-save-feedback');

    const detailFields = {
        nome: document.getElementById('detail-nome'),
        urlLink: document.getElementById('detail-url-link'),
        avatar: document.getElementById('detail-avatar'),
        clero: document.getElementById('detail-clero'),
        setor: document.getElementById('detail-setor'),
        telefone: document.getElementById('detail-telefone'),
        email: document.getElementById('detail-email'),
        telefone: document.getElementById('detail-telefone'),
        email: document.getElementById('detail-email'),
        enderecoOriginal: document.getElementById('detail-endereco-original'),
        enderecoLogradouro: document.getElementById('detail-endereco-logradouro'),
        enderecoNumero: document.getElementById('detail-endereco-numero'),
        enderecoBairro: document.getElementById('detail-endereco-bairro'),
        enderecoCidade: document.getElementById('detail-endereco-cidade'),
        enderecoUF: document.getElementById('detail-endereco-uf'),
        enderecoCEP: document.getElementById('detail-endereco-cep'),
        secretaria: document.getElementById('detail-secretaria'),
        secretaria: document.getElementById('detail-secretaria'),
        missas: document.getElementById('detail-missas'),
        facebook: document.getElementById('detail-facebook'),
        instagram: document.getElementById('detail-instagram'),
        youtube: document.getElementById('detail-youtube'),
        whatsapp: document.getElementById('detail-whatsapp'),
        navCounter: document.getElementById('detail-nav-counter'),
        curadoBadge: document.getElementById('detail-curado-badge'),
        completenessPct: document.getElementById('detail-completeness-pct'),
        completenessFill: document.getElementById('detail-completeness-fill'),
        locais: document.getElementById('detail-locais'),
    };

    // Map field ids to curation-field containers for status coloring
    const fieldContainers = {
        clero: document.getElementById('cf-clero'),
        setor: document.getElementById('cf-setor'),
        telefone: document.getElementById('cf-telefone'),
        email: document.getElementById('cf-email'),
        endereco: document.getElementById('cf-endereco'),
        secretaria: document.getElementById('cf-secretaria'),
        missas: document.getElementById('cf-missas'),
        redes: document.getElementById('cf-redes'),
    };

    function openParishModal(index) {
        currentParishIndex = index;
        populateParishModal(parishDataCached[index], index);
        openModal(modalParishDetail);
    }

    function populateParishModal(p, index) {
        if (!p) return;

        // Header
        detailFields.nome.textContent = p.nome || 'Paróquia sem nome';
        detailFields.urlLink.href = p.url || '#';

        // Avatar
        if (p.imagem_thumbnail) {
            detailFields.avatar.innerHTML = `<img src="${p.imagem_thumbnail}" alt="${p.nome}" onerror="this.outerHTML='<i class=\\"fa-solid fa-church\\"></i>'">`;
        } else {
            detailFields.avatar.innerHTML = `<i class="fa-solid fa-church"></i>`;
        }

        // Nav counter
        detailFields.navCounter.textContent = `${index + 1} / ${parishDataCached.length}`;
        btnDetailPrev.disabled = index <= 0;
        btnDetailNext.disabled = index >= parishDataCached.length - 1;

        // Curado badge
        if (p.curado) {
            detailFields.curadoBadge.classList.remove('hidden');
        } else {
            detailFields.curadoBadge.classList.add('hidden');
        }

        // Text fields
        detailFields.clero.value = getFlatClero(p);
        detailFields.setor.value = p.setor || '';
        detailFields.telefone.value = p.telefone || '';
        detailFields.email.value = p.email || '';
        detailFields.email.value = p.email || '';
        
        let endObj = p.endereco || {};
        detailFields.enderecoOriginal.value = endObj.original || '';
        detailFields.enderecoLogradouro.value = endObj.logradouro || '';
        detailFields.enderecoNumero.value = endObj.numero || '';
        detailFields.enderecoBairro.value = endObj.bairro || '';
        detailFields.enderecoCidade.value = endObj.cidade || '';
        detailFields.enderecoUF.value = endObj.uf || '';
        detailFields.enderecoCEP.value = endObj.cep || '';
        
        detailFields.secretaria.value = getFlatSecretaria(p);
        detailFields.secretaria.value = getFlatSecretaria(p);
        detailFields.missas.value = getFlatMissas(p);

        // Social media
        const redes = p.redes_sociais || {};
        detailFields.facebook.value = redes.facebook && typeof redes.facebook === 'object' ? (redes.facebook.url || '') : (redes.facebook || '');
        detailFields.instagram.value = redes.instagram && typeof redes.instagram === 'object' ? (redes.instagram.url || '') : (redes.instagram || '');
        detailFields.youtube.value = redes.youtube && typeof redes.youtube === 'object' ? (redes.youtube.url || '') : (redes.youtube || '');
        detailFields.whatsapp.value = redes.whatsapp && typeof redes.whatsapp === 'object' ? (redes.whatsapp.url || '') : (redes.whatsapp || '');

        // Locais de Culto
        const locais = p.locais_culto || [];
        if (locais.length > 0) {
            let locaisHtml = '';
            locais.forEach(loc => {
                locaisHtml += `<div class="local-culto-item" style="padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem;">
                    <strong style="color: var(--primary-color); display: block; margin-bottom: 4px;">${loc.nome}</strong>
                    ${loc.endereco ? `<div style="margin-bottom: 2px;"><i class="fa-solid fa-location-dot" style="opacity: 0.7; width: 16px;"></i> ${loc.endereco}</div>` : ''}
                    ${loc.telefone ? `<div style="margin-bottom: 2px;"><i class="fa-solid fa-phone" style="opacity: 0.7; width: 16px;"></i> ${loc.telefone}</div>` : ''}
                    ${loc.email ? `<div><i class="fa-solid fa-envelope" style="opacity: 0.7; width: 16px;"></i> ${loc.email}</div>` : ''}
                </div>`;
            });
            if (detailFields.locais) {
                detailFields.locais.innerHTML = locaisHtml;
            }
        } else {
            if (detailFields.locais) {
                detailFields.locais.innerHTML = '<div style="padding: 12px; font-style: italic; opacity: 0.6;">Nenhuma capela ou comunidade atrelada a esta matriz.</div>';
            }
        }

        // Clear feedback
        showFeedback(detailSaveFeedback, null);

        // Update status indicators
        updateFieldStatuses();
    }

    function updateFieldStatuses() {
        const checks = {
            clero: detailFields.clero.value.trim(),
            setor: detailFields.setor.value.trim(),
            telefone: detailFields.telefone.value.trim(),
            email: detailFields.email.value.trim(),
            endereco: detailFields.enderecoOriginal.value.trim() || detailFields.enderecoLogradouro.value.trim(),
            secretaria: detailFields.secretaria.value.trim(),
            missas: detailFields.missas.value.trim(),
            redes: detailFields.facebook.value.trim() || detailFields.instagram.value.trim() ||
                   detailFields.youtube.value.trim() || detailFields.whatsapp.value.trim(),
        };

        let filled = 0;
        const total = Object.keys(checks).length;

        Object.entries(checks).forEach(([key, val]) => {
            const container = fieldContainers[key];
            if (!container) return;
            if (val) {
                filled++;
                container.classList.remove('field-empty');
                container.classList.add('field-filled');
            } else {
                container.classList.remove('field-filled');
                container.classList.add('field-empty');
            }
        });

        const pct = Math.round((filled / total) * 100);
        detailFields.completenessPct.textContent = `${pct}%`;
        detailFields.completenessFill.style.width = `${pct}%`;
    }

    // Live update status on input
    Object.values(detailFields).forEach(el => {
        if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) {
            el.addEventListener('input', updateFieldStatuses);
        }
    });

    // Navigation
    btnDetailPrev.addEventListener('click', () => {
        if (currentParishIndex > 0) openParishModal(currentParishIndex - 1);
    });

    btnDetailNext.addEventListener('click', () => {
        if (currentParishIndex < parishDataCached.length - 1) openParishModal(currentParishIndex + 1);
    });

    // Keyboard navigation
    modalParishDetail.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') btnDetailPrev.click();
        if (e.key === 'ArrowRight') btnDetailNext.click();
    });

    // ViaCEP Sync Logic
    const btnViacepSync = document.getElementById('btn-viacep-sync');
    const viacepComparison = document.getElementById('viacep-comparison');
    const viacepComparisonBody = document.getElementById('viacep-comparison-body');
    const btnViacepCancel = document.getElementById('btn-viacep-cancel');
    const btnViacepApply = document.getElementById('btn-viacep-apply');

    let pendingViacepData = null;

    if (btnViacepSync) {
        btnViacepSync.addEventListener('click', async () => {
            const cep = detailFields.enderecoCEP.value.replace(/\D/g, '');
            if (cep.length !== 8) {
                alert('Por favor, informe um CEP válido com 8 dígitos.');
                return;
            }

            btnViacepSync.disabled = true;
            btnViacepSync.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

            try {
                let foundData = null;

                // 1. Tenta ViaCEP
                try {
                    const resViacep = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
                    const dataViacep = await resViacep.json();
                    if (!dataViacep.erro && dataViacep.localidade) {
                        foundData = {
                            logradouro: dataViacep.logradouro || '',
                            bairro: dataViacep.bairro || '',
                            localidade: dataViacep.localidade,
                            uf: dataViacep.uf
                        };
                    }
                } catch (e) { console.warn("ViaCEP falhou", e); }

                // 2. Tenta AwesomeAPI como fallback
                if (!foundData) {
                    try {
                        const resAwesome = await fetch(`https://cep.awesomeapi.com.br/json/${cep}`);
                        if (resAwesome.ok) {
                            const dataAwesome = await resAwesome.json();
                            if (dataAwesome.city) {
                                foundData = {
                                    logradouro: dataAwesome.address || '',
                                    bairro: dataAwesome.district || '',
                                    localidade: dataAwesome.city,
                                    uf: dataAwesome.state
                                };
                            }
                        }
                    } catch (e) { console.warn("AwesomeAPI falhou", e); }
                }

                // 3. Tenta BrasilAPI como último fallback
                if (!foundData) {
                    try {
                        const resBrasil = await fetch(`https://brasilapi.com.br/api/cep/v1/${cep}`);
                        if (resBrasil.ok) {
                            const dataBrasil = await resBrasil.json();
                            if (dataBrasil.city) {
                                foundData = {
                                    logradouro: dataBrasil.street || '',
                                    bairro: dataBrasil.neighborhood || '',
                                    localidade: dataBrasil.city,
                                    uf: dataBrasil.state
                                };
                            }
                        }
                    } catch (e) { console.warn("BrasilAPI falhou", e); }
                }

                if (!foundData) {
                    alert('CEP não encontrado nas bases do ViaCEP, AwesomeAPI ou BrasilAPI.');
                    return;
                }

                pendingViacepData = foundData;
                
                // Build comparison table
                const fieldsToCompare = [
                    { id: 'logradouro', name: 'Logradouro', current: detailFields.enderecoLogradouro.value, new: foundData.logradouro },
                    { id: 'bairro', name: 'Bairro', current: detailFields.enderecoBairro.value, new: foundData.bairro },
                    { id: 'cidade', name: 'Cidade', current: detailFields.enderecoCidade.value, new: foundData.localidade },
                    { id: 'uf', name: 'UF', current: detailFields.enderecoUF.value, new: foundData.uf }
                ];

                let html = '';
                fieldsToCompare.forEach(f => {
                    if (f.new && f.new.trim() !== '') {
                        const isDifferent = f.current.trim().toLowerCase() !== f.new.trim().toLowerCase();
                        const isCurrentEmpty = f.current.trim() === '';
                        // Só marca automaticamente se o campo atual estiver vazio
                        const shouldCheck = isCurrentEmpty;

                        html += `
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <td style="padding: 6px 4px; font-weight: bold;">${f.name}</td>
                                <td style="padding: 6px 4px; opacity: 0.7;">${f.current || '<em>(Vazio)</em>'}</td>
                                <td style="padding: 6px 4px; color: #4ade80;">${f.new}</td>
                                <td style="padding: 6px 4px; text-align: center;">
                                    <input type="checkbox" class="viacep-apply-cb" data-field="${f.id}" data-value="${f.new}" ${shouldCheck ? 'checked' : ''} style="cursor: pointer; transform: scale(1.2);">
                                </td>
                            </tr>
                        `;
                    }
                });

                if (html === '') {
                    alert('O ViaCEP não retornou dados úteis adicionais para este CEP.');
                    return;
                }

                viacepComparisonBody.innerHTML = html;
                viacepComparison.classList.remove('hidden');
            } catch (e) {
                alert('Erro ao consultar ViaCEP.');
            } finally {
                btnViacepSync.disabled = false;
                btnViacepSync.innerHTML = '<i class="fa-solid fa-rotate"></i>';
            }
        });

        btnViacepCancel.addEventListener('click', () => {
            viacepComparison.classList.add('hidden');
            pendingViacepData = null;
        });

        btnViacepApply.addEventListener('click', () => {
            const checkboxes = viacepComparisonBody.querySelectorAll('.viacep-apply-cb:checked');
            checkboxes.forEach(cb => {
                const field = cb.dataset.field;
                const val = cb.dataset.value;
                if (field === 'logradouro') detailFields.enderecoLogradouro.value = val;
                if (field === 'bairro') detailFields.enderecoBairro.value = val;
                if (field === 'cidade') detailFields.enderecoCidade.value = val;
                if (field === 'uf') detailFields.enderecoUF.value = val;
            });
            
            updateFieldStatuses();
            viacepComparison.classList.add('hidden');
            pendingViacepData = null;
            
            // Auto-salvar após aplicar
            btnSaveCuration.click();
        });
    }

    // Save curation
    btnSaveCuration.addEventListener('click', () => {
        const p = parishDataCached[currentParishIndex];
        if (!p) return;

        const payload = {
            nome: detailFields.clero.closest('.modal-content').querySelector('#detail-nome') ? p.nome : p.nome,
            clero: detailFields.clero.value.trim() || null,
            setor: detailFields.setor.value.trim() || null,
            telefone: detailFields.telefone.value.trim() || null,
            email: detailFields.email.value.trim() || null,
            endereco: {
                original: detailFields.enderecoOriginal.value.trim(),
                logradouro: detailFields.enderecoLogradouro.value.trim(),
                numero: detailFields.enderecoNumero.value.trim(),
                bairro: detailFields.enderecoBairro.value.trim(),
                cidade: detailFields.enderecoCidade.value.trim(),
                uf: detailFields.enderecoUF.value.trim(),
                cep: detailFields.enderecoCEP.value.trim()
            },
            funcionamento_secretaria: detailFields.secretaria.value.trim() || null,
            horarios_missa_texto: detailFields.missas.value.trim() || null,
            redes_sociais: {
                ...(detailFields.facebook.value.trim() ? { facebook: detailFields.facebook.value.trim() } : {}),
                ...(detailFields.instagram.value.trim() ? { instagram: detailFields.instagram.value.trim() } : {}),
                ...(detailFields.youtube.value.trim() ? { youtube: detailFields.youtube.value.trim() } : {}),
                ...(detailFields.whatsapp.value.trim() ? { whatsapp: detailFields.whatsapp.value.trim() } : {}),
            }
        };

        btnSaveCuration.disabled = true;
        btnSaveCuration.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Salvando...';

        fetch(`/api/data/${activeDioceseId}/${currentParishIndex}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(async res => {
            const data = await res.json();
            if (res.ok) {
                // Update local cache
                if (data.parish) {
                    parishDataCached[currentParishIndex] = data.parish;
                } else {
                    Object.assign(parishDataCached[currentParishIndex], payload);
                    parishDataCached[currentParishIndex].curado = true;
                }
                detailFields.curadoBadge.classList.remove('hidden');
                showFeedback(detailSaveFeedback, '✓ Dados salvos com sucesso!', 'success');
                // Refresh table row
                renderParishTable(parishDataCached);
            } else {
                showFeedback(detailSaveFeedback, data.message || 'Erro ao salvar.', 'error');
            }
        })
        .catch(() => showFeedback(detailSaveFeedback, 'Erro de rede ao salvar.', 'error'))
        .finally(() => {
            btnSaveCuration.disabled = false;
            btnSaveCuration.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Salvar Curadoria';
        });
    });

    // ==========================================
    // EXPORT JSON
    // ==========================================
    btnExportJson.addEventListener('click', () => {
        if (!activeDioceseId) return;
        window.location.href = `/api/export-json/${activeDioceseId}`;
    });

    btnDeleteDiocese.addEventListener('click', () => {
        if (!activeDioceseId || !activeDioceseName) return;
        if (confirm(`Tem certeza absoluta que deseja excluir a configuração e todos os dados salvos da "${activeDioceseName}"? Essa ação não pode ser desfeita.`)) {
            fetch(`/api/dioceses/${activeDioceseId}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        dataViewerPanel.classList.add('hidden');
                        activeDioceseId = null;
                        activeDioceseName = null;
                        loadDiocesesList();
                    } else {
                        alert('Erro ao excluir a diocese.');
                    }
                })
                .catch(() => alert('Erro de rede ao tentar excluir.'));
        }
    });

    // ==========================================
    // SCRAPING / SSE
    // ==========================================
    btnUploadMd.addEventListener('click', () => {
        inputMdFiles.click();
    });

    inputMdFiles.addEventListener('change', () => {
        if (!inputMdFiles.files || inputMdFiles.files.length === 0) return;
        
        const formData = new FormData();
        const customName = document.getElementById('input-md-diocese-name').value;
        if (customName && customName.trim() !== '') {
            formData.append('diocese_name', customName.trim());
        }
        
        for (let i = 0; i < inputMdFiles.files.length; i++) {
            formData.append('files', inputMdFiles.files[i]);
        }
        
        btnUploadMd.disabled = true;
        btnUploadMd.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processando...';
        showFeedback(uploadFeedback, 'Enviando e processando arquivos, aguarde...', 'info');
        
        fetch('/api/upload-md', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json().then(data => ({status: res.status, data})))
        .then(result => {
            if (result.status === 200 && result.data.success) {
                showFeedback(uploadFeedback, '✓ ' + result.data.message, 'success');
                // Refresh dioceses list
                loadDiocesesList();
            } else {
                showFeedback(uploadFeedback, '⚠ ' + (result.data.message || 'Erro no upload.'), 'error');
            }
        })
        .catch(err => {
            showFeedback(uploadFeedback, 'Erro de rede: ' + err, 'error');
        })
        .finally(() => {
            btnUploadMd.disabled = false;
            btnUploadMd.innerHTML = '<i class="fa-solid fa-file-arrow-up"></i> Selecionar Arquivos .md';
            inputMdFiles.value = ''; // Reset input
        });
    });

});
