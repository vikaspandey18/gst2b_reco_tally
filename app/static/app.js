// State
let selectedFile2B = null;
let selectedFileBook = null;
let currentSummaryData = [];

// Drag and Drop Setup
function setupDropzone(zoneId, inputId, type) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        zone.addEventListener(evt, e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(evt => {
        zone.addEventListener(evt, () => zone.classList.add('dragover'));
    });

    ['dragleave', 'drop'].forEach(evt => {
        zone.addEventListener(evt, () => zone.classList.remove('dragover'));
    });

    zone.addEventListener('drop', e => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            input.files = files;
            handleFileSelect(type, input);
        }
    });
}

function handleFileSelect(type, input) {
    const file = input.files[0];
    if (!file) return;

    if (type === '2b') {
        selectedFile2B = file;
        const infoEl = document.getElementById('file-info-2b');
        infoEl.textContent = `✓ ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        document.getElementById('dz-2b').classList.add('file-ready');
    } else if (type === 'book') {
        selectedFileBook = file;
        const infoEl = document.getElementById('file-info-book');
        infoEl.textContent = `✓ ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        document.getElementById('dz-book').classList.add('file-ready');
    }
}

// Switch Tabs
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    if (tabName === 'reco') {
        document.getElementById('tab-btn-reco').classList.add('active');
        document.getElementById('tab-reco').classList.add('active');
    } else {
        document.getElementById('tab-btn-history').classList.add('active');
        document.getElementById('tab-history').classList.add('active');
        loadHistory();
    }
}

// Format Currency
function formatINR(val) {
    return new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(val || 0);
}

// Reconcile API Call
async function startReconciliation() {
    const period = document.getElementById('periodLabel').value.trim();
    if (!period) {
        alert("Please enter a reconciliation period (e.g. August 2025).");
        return;
    }
    if (!selectedFile2B) {
        alert("Please upload the GSTR-2B Excel file.");
        return;
    }
    if (!selectedFileBook) {
        alert("Please upload the Tally Book Excel file.");
        return;
    }

    const btn = document.getElementById('btn-reconcile');
    const btnText = document.getElementById('btn-text');
    const loader = document.getElementById('loader');

    btn.disabled = true;
    btnText.textContent = "Processing & Generating Excel...";
    loader.classList.remove('hidden');

    const formData = new FormData();
    formData.append('period_label', period);
    formData.append('file_2b', selectedFile2B);
    formData.append('file_book', selectedFileBook);

    try {
        const response = await fetch('/api/reconcile', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Reconciliation failed");
        }

        const data = await response.json();
        renderResults(data);
    } catch (err) {
        alert("Error: " + err.message);
    } finally {
        btn.disabled = false;
        btnText.textContent = "⚡ Run Automated Reconciliation";
        loader.classList.add('hidden');
    }
}

function renderResults(data) {
    const session = data.session;
    currentSummaryData = data.gst_summaries || [];

    // Populate Metrics
    document.getElementById('m-total').textContent = session.total_invoices;
    document.getElementById('m-matched').textContent = session.matched_count;
    document.getElementById('m-mismatched').textContent = session.mismatched_count;
    document.getElementById('m-only-book').textContent = session.only_book_count;
    document.getElementById('m-only-2b').textContent = session.only_2b_count;
    const dupEl = document.getElementById('m-duplicate');
    if (dupEl) dupEl.textContent = session.duplicate_count || 0;
    document.getElementById('m-tax-diff').textContent = formatINR(session.total_tax_diff);

    // Download button
    const dlBtn = document.getElementById('btn-download');
    dlBtn.href = session.download_url;

    // Render Summary Table
    renderSummaryTable(currentSummaryData);

    // Show results section
    const resSec = document.getElementById('results-section');
    resSec.classList.remove('hidden');
    resSec.scrollIntoView({ behavior: 'smooth' });
}

function renderSummaryTable(items) {
    const tbody = document.getElementById('summaryTableBody');
    tbody.innerHTML = '';

    if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No records to display.</td></tr>';
        return;
    }

    items.forEach(item => {
        const tr = document.createElement('tr');
        const isMatched = item.status === 'Book And 2B Match';
        const statusClass = isMatched ? 'matched' : (item.status.includes('Only') ? 'only' : 'mismatched');

        tr.innerHTML = `
            <td><strong>${item.gstin}</strong></td>
            <td>₹${formatINR(item.book_taxable)}</td>
            <td>₹${formatINR(item.book_total_tax)}</td>
            <td>₹${formatINR(item.two_b_taxable)}</td>
            <td>₹${formatINR(item.two_b_total_tax)}</td>
            <td style="color:${item.diff_taxable !== 0 ? '#b91c1c' : 'inherit'}">₹${formatINR(item.diff_taxable)}</td>
            <td style="color:${item.diff_total_tax !== 0 ? '#b91c1c' : 'inherit'}">₹${formatINR(item.diff_total_tax)}</td>
            <td><span class="status-pill ${statusClass}">${item.status}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function filterSummaryTable() {
    const filter = document.getElementById('statusFilter').value;
    if (filter === 'ALL') {
        renderSummaryTable(currentSummaryData);
    } else if (filter === 'MATCH') {
        renderSummaryTable(currentSummaryData.filter(i => i.status === 'Book And 2B Match'));
    } else {
        renderSummaryTable(currentSummaryData.filter(i => i.status !== 'Book And 2B Match'));
    }
}

// Load History
async function loadHistory() {
    const tbody = document.getElementById('historyTableBody');
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 2rem;">Loading history...</td></tr>';

    try {
        const res = await fetch('/api/history');
        if (!res.ok) throw new Error("Failed to load history");

        const list = await res.json();
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 2rem;">No previous reconciliation runs found.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        list.forEach(item => {
            const dateStr = new Date(item.created_at).toLocaleString();
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${item.period_label}</strong></td>
                <td>${dateStr}</td>
                <td>${item.file_2b_name || '-'}</td>
                <td>${item.file_book_name || '-'}</td>
                <td>${item.total_invoices}</td>
                <td style="color:#16a34a; font-weight:600;">${item.matched_count}</td>
                <td style="color:#b91c1c; font-weight:600;">${item.mismatched_count}</td>
                <td>₹${formatINR(item.total_tax_diff)}</td>
                <td>
                    <a href="${item.download_url}" class="btn btn-download btn-sm" style="margin-right: 6px;">📥 Download</a>
                    <button class="btn btn-sm" style="background:#fee2e2; color:#b91c1c;" onclick="deleteSession(${item.id})">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" style="color:red; text-align:center;">${err.message}</td></tr>`;
    }
}

async function deleteSession(id) {
    if (!confirm("Are you sure you want to delete this historical record?")) return;
    try {
        await fetch(`/api/history/${id}`, { method: 'DELETE' });
        loadHistory();
    } catch (err) {
        alert("Failed to delete: " + err.message);
    }
}

// Initialize Dropzones on load
window.addEventListener('DOMContentLoaded', () => {
    setupDropzone('dz-2b', 'file2b', '2b');
    setupDropzone('dz-book', 'fileBook', 'book');
});
