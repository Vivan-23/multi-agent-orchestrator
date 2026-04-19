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
elements.promptInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight < 200 ? this.scrollHeight : 200) + 'px';
});

// Handle enter to send
elements.promptInput.addEventListener('keydown', function(e) {
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
            <div class="metric-value" style="font-size: 1.2rem; word-break: break-all; text-align: center;">${modelUsed}</div>
            <div class="metric-label">Model</div>
        </div>
    `;
    elements.dashboardContainer.appendChild(metricsGrid);

    // Insights / Output
    const insightsCard = document.createElement('div');
    insightsCard.className = 'insights-card';
    insightsCard.innerHTML = `<h3>Findings & Insights</h3>`;
    
    let outputData = data.output || data.result || data;
    
    // Parse the output if it's a string that might be JSON
    if (typeof outputData === 'string') {
        try {
            outputData = JSON.parse(outputData);
        } catch(e) {}
    }

    if (typeof outputData === 'object' && !Array.isArray(outputData)) {
        // Build a bullet list from the object
        const ul = document.createElement('ul');
        ul.className = 'insights-list';
        
        const buildList = (obj) => {
            let items = '';
            for (const [key, val] of Object.entries(obj)) {
                if (Array.isArray(val)) {
                    if (val.length === 0) {
                        items += `<li><strong>${key.toUpperCase()}:</strong> None</li>`;
                    } else {
                        let subItems = val.map(v => `<li style="margin-left: 20px;">${typeof v === 'object' ? JSON.stringify(v) : v}</li>`).join('');
                        items += `<li style="margin-bottom: 12px;"><strong>${key.toUpperCase()}:</strong><ul style="margin-top: 8px; margin-bottom: 8px; padding-left: 0; list-style-type: none;">${subItems}</ul></li>`;
                    }
                } else if (typeof val === 'object' && val !== null) {
                    items += `<li><strong>${key.toUpperCase()}:</strong> ${JSON.stringify(val)}</li>`;
                } else {
                    items += `<li><strong>${key.toUpperCase()}:</strong> ${val}</li>`;
                }
            }
            return items;
        }
        
        ul.innerHTML = buildList(outputData);
        insightsCard.appendChild(ul);
    } else {
        // Fallback for string
        const p = document.createElement('p');
        p.style.whiteSpace = 'pre-wrap';
        p.textContent = typeof outputData === 'string' ? outputData : JSON.stringify(outputData, null, 2);
        insightsCard.appendChild(p);
    }
    
    elements.dashboardContainer.appendChild(insightsCard);
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
// Refresh history every 10 seconds
setInterval(fetchHistory, 10000);
