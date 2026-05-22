/**
 * Diocese Scraper - Client-side Interaction JavaScript
 * Author: Antigravity AI
 */

document.addEventListener('DOMContentLoaded', () => {
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
    
    // Data Viewer elements
    const dataViewerPanel = document.getElementById('data-viewer-panel');
    const viewerDioceseName = document.getElementById('viewer-diocese-name');
    const viewerStats = document.getElementById('viewer-stats');
    const searchParishes = document.getElementById('search-parishes');
    const parishesTableBody = document.getElementById('parishes-table-body');
    const btnReScrape = document.getElementById('btn-re-scrape');

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
            
            // Thumbnail image or default icon
            const thumb = p.imagem_thumbnail 
                ? `<img src="${p.imagem_thumbnail}" alt="${p.nome}" onerror="this.outerHTML='<i class=fa-solid fa-church></i>'">`
                : `<i class="fa-solid fa-church"></i>`;
                
            // Clergy
            let clergyHtml = '';
            if (p.clero) {
                // Split clero by commas or newlines if it's structured, otherwise show as block
                const members = p.clero.split('\n').filter(Boolean);
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
            if (p.funcionamento_secretaria) {
                contactsHtml += `<div class="contact-item" title="${p.funcionamento_secretaria}"><i class="fa-solid fa-clock"></i> <span class="address-text text-truncate">${p.funcionamento_secretaria}</span></div>`;
            }
            if (!contactsHtml) contactsHtml = '<span class="text-dark">-</span>';

            // Address
            let addressHtml = '';
            if (p.endereco) {
                addressHtml += `<span class="address-text" title="${p.endereco}">${p.endereco}</span>`;
            } else {
                addressHtml = '<span class="text-dark">-</span>';
            }

            // Social Media
            let socialHtml = '';
            if (p.redes_sociais && Object.keys(p.redes_sociais).length > 0) {
                Object.entries(p.redes_sociais).forEach(([net, link]) => {
                    let icon = 'fa-solid fa-link';
                    if (net === 'facebook') icon = 'fa-brands fa-facebook-f';
                    else if (net === 'instagram') icon = 'fa-brands fa-instagram';
                    else if (net === 'youtube') icon = 'fa-brands fa-youtube';
                    else if (net === 'whatsapp') icon = 'fa-brands fa-whatsapp';
                    
                    socialHtml += `<a href="${link}" target="_blank" class="social-pill ${net}"><i class="${icon}"></i></a>`;
                });
            } else {
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
                            <a href="${p.url}" target="_blank" class="parish-name-link">${p.nome}</a>
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
    }

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
            const clero = (p.clero || '').toLowerCase();
            const email = (p.email || '').toLowerCase();
            const tel = (p.telefone || '').toLowerCase();
            const addr = (p.endereco || '').toLowerCase();
            
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
                previewClero.textContent = p.clero || '-';
                previewTelefone.textContent = p.telefone || '-';
                previewEmail.textContent = p.email || '-';
                previewSecretaria.textContent = p.funcionamento_secretaria || '-';
                previewEndereco.textContent = p.endereco || '-';
                previewMissas.textContent = p.horarios_missa_texto || '-';
                
                // Redes
                let socialText = '';
                if (p.redes_sociais && Object.keys(p.redes_sociais).length > 0) {
                    socialText = Object.keys(p.redes_sociais).join(', ');
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
            appendLog('\n[SISTEMA ERROR] Conexão com o servidor de streaming foi encerrada de forma abrupta.');
            sseSource.close();
            loadDiocesesList();
        };
    }

    btnReScrape.addEventListener('click', () => {
        if (activeDioceseId && activeDioceseName) {
            if (confirm(`Deseja rodar novamente a raspagem completa para "${activeDioceseName}"? Os dados anteriores serão substituídos.`)) {
                startScrapingProcess(activeDioceseId, activeDioceseName);
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
});
