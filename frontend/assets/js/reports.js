/**
 * Smart Financial Reporting Tool (SFRT) - Reports Engine Controller
 */

let reportModal = null;
let currentActiveReport = null;

document.addEventListener("DOMContentLoaded", async () => {
    reportModal = new bootstrap.Modal(document.getElementById("generateReportModal"));

    const period = getStoredPeriod();
    document.getElementById("repStartDate").value = period.start_date;
    document.getElementById("repEndDate").value = period.end_date;

    const urlParams = new URLSearchParams(window.location.search);
    const reportId = urlParams.get("id");
    const action = urlParams.get("action");

    if (reportId) {
        await loadReportById(reportId);
    } else if (action === "new") {
        openGenerateModal();
    } else {
        await loadLatestReport();
    }
});

function onReportTypeChange() {
    const type = document.getElementById("repType").value;
    const cashFlowOpts = document.getElementById("cashFlowOptions");
    if (type === "CASH_FLOW") {
        cashFlowOpts.style.display = "block";
    } else {
        cashFlowOpts.style.display = "none";
    }
}

function openGenerateModal() {
    onReportTypeChange();
    reportModal.show();
}

async function loadLatestReport() {
    try {
        const res = await API.get("/reports");
        if (res.items && res.items.length > 0) {
            renderReportView(res.items[0]);
        }
    } catch (e) {
        console.warn("Could not fetch reports:", e);
    }
}

async function loadReportById(reportId) {
    try {
        const rep = await API.get(`/reports/${reportId}`);
        renderReportView(rep);
    } catch (err) {
        showToast("Report not found or unavailable.", "danger");
    }
}

document.getElementById("generateReportForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("generateSubmitBtn");
    const btnText = document.getElementById("genBtnText");
    const btnSpinner = document.getElementById("genBtnSpinner");

    btn.disabled = true;
    btnText.textContent = "Crunching Financial Data...";
    btnSpinner.classList.remove("d-none");

    const user = API.getCurrentUser() || {};
    const payload = {
        report_type: document.getElementById("repType").value,
        title: document.getElementById("repTitle").value.trim() || null,
        start_date: document.getElementById("repStartDate").value,
        end_date: document.getElementById("repEndDate").value,
        currency: user.default_currency || "INR",
        opening_cash_balance: parseFloat(document.getElementById("repOpeningCash").value) || 0.0,
        notes: document.getElementById("repNotes").value.trim() || null
    };

    try {
        const report = await API.post("/reports/generate", payload);
        reportModal.hide();
        showToast("Report generated successfully!", "success");
        renderReportView(report);
    } catch (err) {
        alert(err.message || "Failed to generate report.");
    } finally {
        btn.disabled = false;
        btnText.innerHTML = '<i class="bi bi-play-circle me-1"></i> Generate Report';
        btnSpinner.classList.add("d-none");
    }
});

function renderReportView(report) {
    currentActiveReport = report;
    const container = document.getElementById("activeReportContainer");
    const currency = report.currency || "INR";

    const summary = report.summary_metrics || {};
    const details = report.detailed_data || {};
    const params = report.report_parameters || {};
    const warnings = params.data_quality_warnings || [];

    let summaryCardsHtml = "";
    Object.entries(summary).forEach(([k, v]) => {
        const label = k.replace(/_/g, " ").toUpperCase();
        let valStr = "";
        if (typeof v === "number") {
            if (k.includes("pct") || k.includes("margin") || k.includes("ratio")) {
                valStr = `${v.toFixed(1)}%`;
            } else if (k.includes("count")) {
                valStr = v.toLocaleString();
            } else {
                valStr = formatMoney(v, currency);
            }
        } else if (v === null) {
            valStr = "N/A";
        } else {
            valStr = v;
        }

        summaryCardsHtml += `
            <div class="col-md-3 col-sm-6">
                <div class="kpi-card bg-light border-0">
                    <div class="kpi-title">${label}</div>
                    <div class="kpi-value fs-4">${valStr}</div>
                </div>
            </div>
        `;
    });

    // Monthly breakdown table
    const monthly = details.monthly_breakdown || [];
    let monthlyHtml = "";
    if (monthly.length > 0) {
        monthlyHtml = `
            <div class="card-custom mb-4 bg-white">
                <div class="card-header-clean">
                    <h6 class="card-title-clean">Monthly Performance Breakdown</h6>
                </div>
                <div class="table-responsive">
                    <table class="table table-custom">
                        <thead>
                            <tr>
                                <th>Period</th>
                                <th class="text-end">Income</th>
                                <th class="text-end">Expenses</th>
                                <th class="text-end">Net Movement</th>
                                <th class="text-end">Revenue</th>
                                <th class="text-end">Net Profit</th>
                                <th class="text-center">Txs</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${monthly.map(m => `
                                <tr>
                                    <td class="fw-bold">${m.period}</td>
                                    <td class="text-end text-success">${formatMoney(m.income, currency)}</td>
                                    <td class="text-end text-danger">${formatMoney(m.expense, currency)}</td>
                                    <td class="text-end fw-semibold ${m.net >= 0 ? 'text-primary' : 'text-danger'}">${formatMoney(m.net, currency)}</td>
                                    <td class="text-end text-muted">${formatMoney(m.revenue, currency)}</td>
                                    <td class="text-end text-muted">${formatMoney(m.net_profit, currency)}</td>
                                    <td class="text-center text-muted">${m.transaction_count}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // Category breakdown table
    const categories = details.categories || details.expense_categories || details.income_categories || [];
    let catHtml = "";
    if (categories.length > 0) {
        catHtml = `
            <div class="card-custom mb-4 bg-white">
                <div class="card-header-clean">
                    <h6 class="card-title-clean">Category Distribution Breakdown</h6>
                </div>
                <div class="table-responsive">
                    <table class="table table-custom">
                        <thead>
                            <tr>
                                <th>Category</th>
                                <th>Type</th>
                                <th class="text-end">Total Amount</th>
                                <th class="text-end">Percentage Share</th>
                                <th class="text-center">Txs</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${categories.map(c => `
                                <tr>
                                    <td class="fw-semibold">${c.category_name}</td>
                                    <td><span class="badge bg-light text-dark border">${c.category_type}</span></td>
                                    <td class="text-end fw-bold">${formatMoney(c.total_amount, currency)}</td>
                                    <td class="text-end">${c.percentage ? c.percentage.toFixed(1) : 0}%</td>
                                    <td class="text-center">${c.transaction_count}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // Warnings Box
    let warningsHtml = "";
    if (warnings.length > 0) {
        warningsHtml = `
            <div class="alert alert-warning py-2 mb-4 rounded-3 small">
                <i class="bi bi-exclamation-triangle-fill me-1"></i>
                <strong>Data Quality Notice:</strong> ${warnings.join(" ")}
            </div>
        `;
    }

    container.innerHTML = `
        <div class="card-custom p-4 bg-white mb-4 shadow-sm">
            <!-- Report Header Actions -->
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 border-bottom pb-3 mb-4">
                <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="badge bg-primary-light text-primary fw-bold">${report.report_type.replace(/_/g, ' ')}</span>
                        <span class="badge bg-success text-white">STATUS: ${report.generation_status}</span>
                    </div>
                    <h2 class="fw-bold text-dark mb-1">${report.title}</h2>
                    <div class="text-muted small">
                        Period: <strong>${formatDate(report.start_date)}</strong> to <strong>${formatDate(report.end_date)}</strong> &bull; Currency: <strong>${currency}</strong> &bull; Generated: <strong>${formatDate(report.created_at)}</strong>
                    </div>
                </div>

                <div class="d-flex gap-2">
                    <a href="${API_BASE_URL}/reports/${report.id}/export?format=pdf" class="btn btn-sm btn-outline-danger d-flex align-items-center gap-1">
                        <i class="bi bi-file-earmark-pdf"></i> Download PDF
                    </a>
                    <a href="${API_BASE_URL}/reports/${report.id}/export?format=csv" class="btn btn-sm btn-outline-success d-flex align-items-center gap-1">
                        <i class="bi bi-file-earmark-spreadsheet"></i> Export CSV
                    </a>
                    <button class="btn btn-sm btn-light border d-flex align-items-center gap-1" onclick="window.print()">
                        <i class="bi bi-printer"></i> Print
                    </button>
                </div>
            </div>

            ${warningsHtml}

            <!-- Executive Summary Cards -->
            <h5 class="fw-bold mb-3">Executive Summary Metrics</h5>
            <div class="row g-3 mb-4">
                ${summaryCardsHtml}
            </div>

            ${monthlyHtml}
            ${catHtml}

            <!-- Methodology & Notes -->
            <div class="p-3 bg-light rounded-3 border mt-4">
                <div class="fw-bold small text-dark mb-1"><i class="bi bi-info-circle me-1"></i> Calculation Methodology & Audit Notes</div>
                <p class="small text-muted mb-2">${params.methodology || "Standard financial accounting classification rules applied."}</p>
                ${report.notes ? `<p class="small text-muted mb-0"><strong>Auditor Remarks:</strong> ${report.notes}</p>` : ''}
            </div>
        </div>
    `;
}
