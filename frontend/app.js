const API_BASE = 'http://localhost:8000';

const elements = {
    historyList: document.getElementById('history-list'),
    newRunBtn: document.getElementById('new-run-btn'),
    promptInput: document.getElementById('prompt-input'),
    sendBtn: document.getElementById('send-btn'),
    dashboardContainer: document.getElementById('dashboard-container'),
    modelSelect: document.getElementById('model-select'),
    logsContainer: document.getElementById('logs-container'),
    logsContent: document.getElementById('logs-content'),
    currentStateTitle: document.getElementById('current-state-title')
};

let currentRunId = null;
let isProcessing = false;

// Auto-resize textarea
elements.promptInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight < 200 ? this.scrollHeight : 200) + 'px';
});

// Handle enter to send
elements.promptInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

elements.sendBtn.addEventListener('click', handleSend);
elements.newRunBtn.addEventListener('click', startNewRun);

async function fetchHistory() {
    try {
        const res = await fetch(`${API_BASE}/runs`);
        if (!res.ok) throw new Error("Failed to fetch history");
        const runs = await res.json();

        if (runs.error) {
            console.warn("No runs found or API error:", runs.error);
            elements.historyList.innerHTML = '<div class="history-item" style="pointer-events: none; opacity: 0.5;">No previous scans</div>';
            return;
        }

        elements.historyList.innerHTML = '';
        if (!Array.isArray(runs) || runs.length === 0) {
            elements.historyList.innerHTML = '<div class="history-item" style="pointer-events: none; opacity: 0.5;">No previous scans</div>';
            return;
        }

        runs.forEach(run => {
            const el = document.createElement('div');
            el.className = 'history-item';

            const timeStr = run.timestamp ? new Date(run.timestamp).toLocaleString() : 'Past Run';
            let previewText = run.input || 'Agent Execution';
            if (previewText.length > 35) {
                previewText = previewText.substring(0, 35) + '...';
            }

            el.innerHTML = `
                <div class="history-time">${timeStr}</div>
                <div class="history-preview">${previewText}</div>
            `;

            el.onclick = () => loadRun(run, el);

            if (currentRunId && run.run_id === currentRunId) {
                el.classList.add('active');
            }

            elements.historyList.appendChild(el);
        });
    } catch (err) {
        console.error("Error fetching history:", err);
        elements.historyList.innerHTML = '<div style="color: #ef4444; padding: 10px;">Failed to load history. Ensure API is running.</div>';
    }
}

function startNewRun() {
    currentRunId = null;
    elements.dashboardContainer.innerHTML = `
        <div class="welcome-message">
            <div class="gradient-text huge">Ready for Recon.</div>
            <p>Enter a target domain or prompt to start the cybersecurity reconnaissance agent.</p>
        </div>
    `;
    elements.logsContainer.classList.add('hidden');
    const details = elements.logsContainer.querySelector('details');
    if (details) details.removeAttribute('open');
    elements.currentStateTitle.textContent = "New Scan";
    elements.promptInput.value = '';
    elements.promptInput.style.height = 'auto';
    elements.promptInput.focus();

    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
}

async function handleSend() {
    const text = elements.promptInput.value.trim();
    if (!text || isProcessing) return;

    // Clear welcome message if it's the first message
    const welcomeMsg = elements.dashboardContainer.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    elements.dashboardContainer.innerHTML = ''; // clear previous

    elements.promptInput.value = '';
    elements.promptInput.style.height = 'auto';
    setProcessing(true);
    elements.logsContainer.classList.add('hidden');
    const details = elements.logsContainer.querySelector('details');
    if (details) details.removeAttribute('open');

    const loader = showLoader();

    try {
        const res = await fetch(`${API_BASE}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                input: text,
                model: elements.modelSelect.value
            })
        });

        const data = await res.json();
        loader.remove();

        currentRunId = data.run_id || null;

        renderDashboard(data);

        fetchHistory();

        if (currentRunId) {
            fetchLogs(currentRunId);
        }

    } catch (err) {
        loader.remove();
        elements.dashboardContainer.innerHTML = `<div style="color: #f87171; padding: 20px;">Error: Failed to connect to the agent backend.</div>`;
        console.error(err);
    } finally {
        setProcessing(false);
    }
}

function renderDashboard(data) {
    elements.dashboardContainer.innerHTML = '';

    // Header
    const header = document.createElement('div');
    header.className = 'target-header';
    header.innerHTML = `Recon Results for: <span>${data.input || 'Unknown Target'}</span>`;
    elements.dashboardContainer.appendChild(header);

    // Metrics Grid
    const metricsGrid = document.createElement('div');
    metricsGrid.className = 'metrics-grid';

    const metrics = data.metrics || {};
    const evalScore = metrics.eval_score !== undefined ? metrics.eval_score + '/100' : 'N/A';
    const errors = data.errors !== undefined ? data.errors : '0';
    const modelUsed = data.model_used || data.model || 'Unknown';
    const stepsCount = (data.metrics && data.metrics.steps_count !== undefined) ? data.metrics.steps_count : (data.steps ? data.steps.length : '0');

    metricsGrid.innerHTML = `
        <div class="metric-card">
            <div class="metric-value">${evalScore}</div>
            <div class="metric-label">Eval Score</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: ${errors > 0 ? '#f87171' : '#4ade80'}">${errors}</div>
            <div class="metric-label">Errors</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">${stepsCount}</div>
            <div class="metric-label">Steps</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1.1rem; word-break: break-all; text-align: center;">${modelUsed}</div>
            <div class="metric-label">Model</div>
        </div>
    `;
    elements.dashboardContainer.appendChild(metricsGrid);

    // Parse output
    let outputData = data.output || data.result || data;
    if (typeof outputData === 'string') {
        try {
            outputData = JSON.parse(outputData);
        } catch (e) { }
    }

    // Main Report Card
    const reportCard = document.createElement('div');
    reportCard.className = 'insights-card';

    if (typeof outputData === 'object' && outputData !== null && !Array.isArray(outputData)) {
        const risk = (outputData.risk_level || 'low').toLowerCase();
        let riskColor = '#4ade80';
        let riskBg = 'rgba(74, 222, 128, 0.1)';
        let riskBorder = 'rgba(74, 222, 128, 0.2)';
        if (risk === 'high') {
            riskColor = '#f87171';
            riskBg = 'rgba(248, 113, 113, 0.1)';
            riskBorder = 'rgba(248, 113, 113, 0.2)';
        } else if (risk === 'medium') {
            riskColor = '#fbbf24';
            riskBg = 'rgba(251, 191, 36, 0.1)';
            riskBorder = 'rgba(251, 191, 36, 0.2)';
        }

        let htmlContent = `
            <div class="report-section risk-overview-section" style="display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 24px; padding: 16px; background: ${riskBg}; border: 1px solid ${riskBorder}; border-radius: 12px;">
                <div>
                    <span style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">Risk Assessment</span>
                    <h2 style="font-size: 1.8rem; font-weight: 700; margin-top: 4px; color: ${riskColor}; text-transform: capitalize;">${risk} Risk</h2>
                </div>
                <div class="risk-badge-icon" style="font-size: 2.5rem;">
                    ${risk === 'high' ? '⚠️' : risk === 'medium' ? '⚡' : '🛡️'}
                </div>
            </div>
            
            <div class="report-section summary-section" style="margin-bottom: 24px;">
                <h3 style="font-size: 1.15rem; margin-bottom: 8px; color: #fff;">Executive Summary</h3>
                <p style="color: var(--text-main); font-size: 0.95rem; line-height: 1.6; background: rgba(255,255,255,0.02); padding: 16px; border-radius: 10px; border: 1px solid var(--border-color);">${outputData.summary || 'No summary available.'}</p>
            </div>
        `;

        // Technologies Section
        const techs = outputData.technologies || [];
        if (techs.length > 0) {
            htmlContent += `
                <div class="report-section tech-section" style="margin-bottom: 24px;">
                    <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: #fff;">Technologies Detected</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${techs.map(t => `<span class="tech-tag" style="background: rgba(138, 43, 226, 0.1); border: 1px solid rgba(138, 43, 226, 0.25); color: #c084fc; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">${t}</span>`).join('')}
                    </div>
                </div>
            `;
        }

        // Subdomains Section
        const subs = outputData.subdomains || [];
        if (subs.length > 0) {
            const visibleSubs = subs.slice(0, 7);
            const remainingSubs = subs.slice(7);

            let subsHtml = visibleSubs.map(s => `
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; font-family: monospace; font-size: 0.9rem;">
                    <span style="color: #60a5fa;">${s}</span>
                    <button onclick="navigator.clipboard.writeText('${s}'); alert('Copied: ${s}')" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.8rem;" title="Copy">❒</button>
                </div>
            `).join('');

            if (remainingSubs.length > 0) {
                subsHtml += `
                    <details class="subdomains-dropdown" style="margin-top: 8px; outline: none;">
                        <summary style="cursor: pointer; color: #388bfd; font-size: 0.9rem; font-weight: 600; outline: none; user-select: none; display: inline-flex; align-items: center; gap: 4px;">
                            <span>Show More (${remainingSubs.length} more)</span>
                        </summary>
                        <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px;">
                            ${remainingSubs.map(s => `
                                <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; font-family: monospace; font-size: 0.9rem;">
                                    <span style="color: #60a5fa;">${s}</span>
                                    <button onclick="navigator.clipboard.writeText('${s}'); alert('Copied: ${s}')" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.8rem;" title="Copy">❒</button>
                                </div>
                            `).join('')}
                        </div>
                    </details>
                `;
            }

            htmlContent += `
                <div class="report-section subdomains-section" style="margin-bottom: 24px;">
                    <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: #fff;">Exposed Subdomains (${subs.length})</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        ${subsHtml}
                    </div>
                </div>
            `;
        }

        // Endpoints Section
        const ends = outputData.endpoints || [];
        if (ends.length > 0) {
            htmlContent += `
                <div class="report-section endpoints-section" style="margin-bottom: 24px;">
                    <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: #fff;">Scanned Endpoints (${ends.length})</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        ${ends.map(e => `
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; font-family: monospace; font-size: 0.9rem;">
                                <a href="${e}" target="_blank" style="color: #388bfd; text-decoration: none; word-break: break-all;">${e}</a>
                                <button onclick="navigator.clipboard.writeText('${e}'); alert('Copied: ${e}')" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.8rem;" title="Copy">❒</button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Insights Section
        const insights = outputData.insights || [];
        if (insights.length > 0) {
            htmlContent += `
                <div class="report-section insights-section" style="margin-bottom: 24px;">
                    <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: #fff;">Security Analysis & Flaws</h3>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        ${insights.map(ins => `
                            <div class="insight-alert" style="display: flex; gap: 12px; padding: 14px 16px; background: rgba(255, 255, 255, 0.03); border-left: 4px solid #8a2be2; border-top: 1px solid var(--border-color); border-right: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); border-radius: 0 8px 8px 0; font-size: 0.92rem; line-height: 1.5;">
                                <div style="color: #a855f7; font-size: 1.1rem; font-weight: bold;">🔎</div>
                                <div style="color: var(--text-main);">${ins}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Citations Section
        const cites = outputData.citations || [];
        if (cites.length > 0) {
            htmlContent += `
                <div class="report-section citations-section" style="margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border-color);">
                    <h4 style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 8px;">Sources & Citations:</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${cites.map(c => `<a href="${c}" target="_blank" style="background: rgba(255,255,255,0.04); border: 1px solid var(--border-color); color: var(--text-muted); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; text-decoration: none; transition: all 0.2s;" onmouseover="this.style.color='#fff'; this.style.borderColor='rgba(255,255,255,0.2)'" onmouseout="this.style.color='var(--text-muted)'; this.style.borderColor='var(--border-color)'">${c}</a>`).join('')}
                    </div>
                </div>
            `;
        }

        reportCard.innerHTML = htmlContent;
    } else {
        const p = document.createElement('p');
        p.style.whiteSpace = 'pre-wrap';
        p.style.lineHeight = '1.6';
        p.textContent = typeof outputData === 'string' ? outputData : JSON.stringify(outputData, null, 2);
        reportCard.appendChild(p);
    }

    elements.dashboardContainer.appendChild(reportCard);
}

function showLoader() {
    elements.dashboardContainer.innerHTML = '';
    const loaderDiv = document.createElement('div');
    loaderDiv.className = `loader-wrapper`;
    loaderDiv.innerHTML = `
        <div class="metric-card" style="width: fit-content; margin: 0 auto;">
            <div class="typing-indicator" style="padding: 10px;">
                <span></span><span></span><span></span>
            </div>
            <div class="metric-label" style="margin-top: 8px;">Agent Analyzing...</div>
        </div>
    `;
    elements.dashboardContainer.appendChild(loaderDiv);
    const contentBody = document.getElementById('content-body');
    contentBody.scrollTop = contentBody.scrollHeight;
    return loaderDiv;
}

function setProcessing(processing) {
    isProcessing = processing;
    elements.sendBtn.disabled = processing;
    if (!processing) elements.promptInput.focus();
}

async function loadRun(run, el) {
    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
    if (el) el.classList.add('active');

    currentRunId = run.run_id || null;
    elements.dashboardContainer.innerHTML = '';
    elements.currentStateTitle.textContent = `Scan Details`;

    renderDashboard(run);

    if (run.run_id) {
        fetchLogs(run.run_id);
    } else {
        elements.logsContainer.classList.add('hidden');
        const details = elements.logsContainer.querySelector('details');
        if (details) details.removeAttribute('open');
    }
}

async function fetchLogs(runId) {
    if (!runId) return;
    try {
        const res = await fetch(`${API_BASE}/logs/${runId}`);
        if (!res.ok) throw new Error("Failed to fetch logs");
        const logs = await res.json();

        elements.logsContainer.classList.remove('hidden');
        if (logs.length === 0) {
            elements.logsContent.textContent = "No logs available for this run.";
        } else {
            elements.logsContent.textContent = logs.map(l => JSON.stringify(l, null, 2)).join('\n\n');
        }

        setTimeout(() => {
            const contentBody = document.getElementById('content-body');
            contentBody.scrollTop = contentBody.scrollHeight;
        }, 100);
    } catch (err) {
        console.error("Error fetching logs:", err);
    }
}

// Initial fetch
fetchHistory();
// Refresh history every 15 seconds
setInterval(fetchHistory, 15000);
