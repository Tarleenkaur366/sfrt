/**
 * Smart Financial Reporting Tool (SFRT) - Dashboard Controller
 */

let trendsChartInstance = null;
let categoryChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    loadPageData();
});

async function loadPageData() {
    const period = getStoredPeriod();
    const user = API.getCurrentUser() || {};
    const currency = user.default_currency || "INR";

    // Update topbar title
    const titleEl = document.getElementById("topbarPageTitle");
    if (titleEl) {
        titleEl.innerHTML = `
            <h1 class="page-title">Financial Dashboard</h1>
            <p class="page-subtitle">${period.label}: ${formatDate(period.start_date)} to ${formatDate(period.end_date)}</p>
        `;
    }

    try {
        // 1. Fetch Summary
        const summary = await API.get("/dashboard/summary", {
            start_date: period.start_date,
            end_date: period.end_date,
            currency: currency
        });
        renderSummaryKPIs(summary, currency);
        renderAlerts(summary.alerts);
        renderRecentTransactions(summary.recent_transactions, currency);
        renderRecentReports(summary.recent_reports);

        // 2. Fetch Trends Chart Data
        const trends = await API.get("/dashboard/trends", {
            start_date: period.start_date,
            end_date: period.end_date,
            currency: currency
        });
        renderTrendsChart(trends, currency);

        // 3. Fetch Category Breakdown
        const cats = await API.get("/dashboard/category-distribution", {
            category_type: "EXPENSE",
            start_date: period.start_date,
            end_date: period.end_date,
            currency: currency
        });
        renderCategoryChart(cats, currency);

    } catch (err) {
        console.error("Dashboard data load error:", err);
        showToast(err.message || "Unable to fetch dashboard metrics.", "danger");
    }
}

function renderSummaryKPIs(data, currency) {
    document.getElementById("kpiTotalIncome").textContent = formatMoney(data.total_income, currency);
    document.getElementById("kpiAvgIncome").textContent = formatMoney(data.avg_monthly_income, currency);

    document.getElementById("kpiTotalExpenses").textContent = formatMoney(data.total_expenses, currency);
    document.getElementById("kpiAvgExpenses").textContent = formatMoney(data.avg_monthly_expenses, currency);

    const surplusEl = document.getElementById("kpiNetSurplus");
    surplusEl.textContent = formatMoney(data.net_surplus_deficit, currency);
    if (data.net_surplus_deficit < 0) {
        surplusEl.className = "kpi-value text-danger";
    } else {
        surplusEl.className = "kpi-value text-primary";
    }
    document.getElementById("kpiNetCash").textContent = formatMoney(data.net_cash_movement, currency);

    // Margins
    document.getElementById("kpiGrossMargin").textContent = data.gross_profit_margin !== null ? `${data.gross_profit_margin.toFixed(1)}%` : "N/A";
    document.getElementById("kpiGrossProfit").textContent = formatMoney(data.gross_profit, currency);

    document.getElementById("kpiNetMargin").textContent = data.net_profit_margin !== null ? `${data.net_profit_margin.toFixed(1)}%` : "N/A";
    document.getElementById("kpiNetProfit").textContent = formatMoney(data.net_profit, currency);

    document.getElementById("kpiExpenseRatio").textContent = data.expense_to_income_ratio !== null ? `${data.expense_to_income_ratio.toFixed(1)}%` : "N/A";
    document.getElementById("kpiRevenueGrowth").textContent = data.revenue_growth !== null ? formatPct(data.revenue_growth) : "N/A";

    document.getElementById("kpiTxCount").textContent = `${data.total_transactions} txs`;
    document.getElementById("kpiReportsCount").textContent = data.reports_generated_count;
}

function renderAlerts(alerts) {
    const container = document.getElementById("dashboardAlerts");
    if (!alerts || alerts.length === 0) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = alerts.map(a => `
        <div class="alert alert-${a.type} d-flex align-items-center justify-content-between py-2 px-3 mb-2 rounded-3">
            <div class="d-flex align-items-center gap-2">
                <i class="bi ${a.type === 'danger' ? 'bi-exclamation-octagon-fill' : a.type === 'warning' ? 'bi-exclamation-triangle-fill' : 'bi-info-circle-fill'}"></i>
                <div>
                    <strong class="me-1">${a.title}:</strong>
                    <span>${a.message}</span>
                </div>
            </div>
            <button type="button" class="btn-close btn-sm" onclick="this.closest('.alert').remove()"></button>
        </div>
    `).join("");
}

function renderRecentTransactions(txs, currency) {
    const tbody = document.getElementById("recentTransactionsTableBody");
    if (!txs || txs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-4 text-muted">
                    <i class="bi bi-inbox fs-3 d-block mb-2 text-muted"></i>
                    No transactions recorded for this period.
                    <div class="mt-2">
                        <a href="transactions.html?action=new" class="btn btn-sm btn-primary-custom">Add First Transaction</a>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = txs.map(tx => {
        let badgeClass = "badge-transfer";
        if (tx.transaction_type === "Revenue") badgeClass = "badge-revenue";
        else if (tx.transaction_type === "Other Income") badgeClass = "badge-other-income";
        else if (tx.transaction_type === "Operating Expense") badgeClass = "badge-operating-expense";
        else if (tx.transaction_type === "Cost of Goods Sold") badgeClass = "badge-cogs";

        const isIncome = ["Revenue", "Other Income"].includes(tx.transaction_type);
        const amtColor = isIncome ? "text-success" : (tx.transaction_type.includes("Expense") || tx.transaction_type === "Cost of Goods Sold" ? "text-danger" : "text-dark");

        return `
            <tr>
                <td class="text-nowrap text-muted small">${formatDate(tx.transaction_date)}</td>
                <td>
                    <div class="fw-semibold text-truncate" style="max-width: 200px;">${tx.description}</div>
                    <small class="text-muted">${tx.category_name || "Uncategorized"}</small>
                    ${tx.is_sample ? '<span class="badge badge-sample ms-1">SAMPLE</span>' : ''}
                </td>
                <td>
                    <span class="badge-classification ${badgeClass}">${tx.transaction_type}</span>
                </td>
                <td class="text-end fw-bold ${amtColor}">
                    ${isIncome ? '+' : '-'}${formatMoney(tx.amount, currency)}
                </td>
            </tr>
        `;
    }).join("");
}

function renderRecentReports(reports) {
    const container = document.getElementById("recentReportsContainer");
    if (!reports || reports.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="bi bi-file-earmark-bar-graph fs-3 d-block mb-2 text-muted"></i>
                No reports generated yet.
                <div class="mt-2">
                    <a href="reports.html" class="btn btn-sm btn-outline-custom">Generate First Report</a>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = reports.map(r => `
        <div class="d-flex align-items-center justify-content-between p-2 mb-2 bg-light rounded-3">
            <div class="overflow-hidden me-2">
                <div class="fw-semibold text-truncate small">${r.title}</div>
                <small class="text-muted d-block" style="font-size: 0.75rem;">
                    ${r.report_type.replace('_', ' ')} &bull; ${formatDate(r.start_date)} to ${formatDate(r.end_date)}
                </small>
            </div>
            <div class="d-flex gap-1 flex-shrink-0">
                <a href="${API_BASE_URL}/reports/${r.id}/export?format=pdf" class="btn btn-sm btn-outline-danger py-1 px-2" title="Download PDF">
                    <i class="bi bi-file-pdf"></i>
                </a>
                <a href="${API_BASE_URL}/reports/${r.id}/export?format=csv" class="btn btn-sm btn-outline-success py-1 px-2" title="Download CSV">
                    <i class="bi bi-file-earmark-spreadsheet"></i>
                </a>
            </div>
        </div>
    `).join("");
}

function renderTrendsChart(data, currency) {
    const ctx = document.getElementById("trendsChart").getContext("2d");
    if (trendsChartInstance) trendsChartInstance.destroy();

    const labels = data.periods && data.periods.length > 0 ? data.periods : ["No Data"];
    const incomeData = data.income || [0];
    const expenseData = data.expenses || [0];
    const netData = data.net || [0];

    trendsChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    type: "bar",
                    label: "Income",
                    data: incomeData,
                    backgroundColor: "rgba(16, 185, 129, 0.75)",
                    borderColor: "#10b981",
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    type: "bar",
                    label: "Expenses",
                    data: expenseData,
                    backgroundColor: "rgba(239, 68, 68, 0.75)",
                    borderColor: "#ef4444",
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    type: "line",
                    label: "Net Operating Surplus",
                    data: netData,
                    borderColor: "#0284c7",
                    backgroundColor: "rgba(2, 132, 199, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false,
                    pointBackgroundColor: "#0284c7"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top", labels: { boxWidth: 12, font: { size: 12 } } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${formatMoney(ctx.parsed.y, currency)}`
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    ticks: {
                        callback: (val) => `${currency} ${val >= 1000 ? (val/1000).toFixed(0) + 'k' : val}`
                    }
                }
            }
        }
    });
}

function renderCategoryChart(data, currency) {
    const ctx = document.getElementById("categoryChart").getContext("2d");
    if (categoryChartInstance) categoryChartInstance.destroy();

    const labels = data.labels && data.labels.length > 0 ? data.labels : ["No Outlays"];
    const values = data.values && data.values.length > 0 ? data.values : [1];

    categoryChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "#0284c7", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6",
                    "#ec4899", "#14b8a6", "#64748b", "#f97316", "#06b6d4"
                ],
                borderWidth: 2,
                borderColor: "#ffffff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.label}: ${formatMoney(ctx.parsed, currency)}`
                    }
                }
            },
            cutout: "68%"
        }
    });
}
