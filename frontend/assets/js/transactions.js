/**
 * Smart Financial Reporting Tool (SFRT) - Transaction Management Controller
 */

let currentPage = 1;
const pageSize = 15;
let currentCategories = [];
let txModalInstance = null;

document.addEventListener("DOMContentLoaded", async () => {
    txModalInstance = new bootstrap.Modal(document.getElementById("transactionModal"));
    
    // Set default date for form to today
    document.getElementById("txDate").value = new Date().toISOString().split("T")[0];

    // Set currency prefix
    const user = API.getCurrentUser() || {};
    const curr = user.default_currency || "INR";
    const prefix = curr === "INR" ? "₹" : (curr === "USD" ? "$" : (curr === "EUR" ? "€" : curr));
    document.getElementById("formCurrencyPrefix").textContent = prefix;

    await loadCategories();
    await loadTransactions();

    // Check if ?action=new is in query string
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("action") === "new") {
        openAddTransactionModal();
    }
});

async function loadCategories() {
    try {
        currentCategories = await API.get("/categories");
        const filterCat = document.getElementById("filterCategory");
        const txCat = document.getElementById("txCategory");

        filterCat.innerHTML = `<option value="">All Categories</option>`;
        txCat.innerHTML = `<option value="">Uncategorized</option>`;

        currentCategories.forEach(c => {
            filterCat.innerHTML += `<option value="${c.id}">${c.name} (${c.category_type})</option>`;
            txCat.innerHTML += `<option value="${c.id}">${c.name}</option>`;
        });
    } catch (e) {
        console.warn("Could not load categories:", e);
    }
}

async function loadTransactions(page = 1) {
    currentPage = page;
    const tbody = document.getElementById("transactionsTbody");
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-5 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading transactions...
            </td>
        </tr>
    `;

    const user = API.getCurrentUser() || {};
    const currency = user.default_currency || "INR";

    const params = {
        page: currentPage,
        page_size: pageSize,
        search: document.getElementById("filterSearch").value.trim(),
        transaction_type: document.getElementById("filterType").value,
        category_id: document.getElementById("filterCategory").value,
        start_date: document.getElementById("filterStartDate").value,
        end_date: document.getElementById("filterEndDate").value,
        sort_by: document.getElementById("sortField").value,
        sort_dir: document.getElementById("sortDir").value,
        currency: currency
    };

    try {
        const res = await API.get("/transactions", params);
        renderTransactionRows(res.items, currency);
        renderPagination(res.page, res.total_pages, res.total);
        document.getElementById("txCountBadge").textContent = `${res.total} records`;
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">${err.message}</td></tr>`;
    }
}

function renderTransactionRows(items, currency) {
    const tbody = document.getElementById("transactionsTbody");
    if (!items || items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-inbox"></i></div>
                        <div class="empty-state-title">No Transactions Found</div>
                        <div class="empty-state-text">No records matched the selected filters. Add a new record or reset the search filters.</div>
                        <button class="btn btn-sm btn-primary-custom" onclick="openAddTransactionModal()">Add Transaction</button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = items.map(tx => {
        let badgeClass = "badge-transfer";
        if (tx.transaction_type === "Revenue") badgeClass = "badge-revenue";
        else if (tx.transaction_type === "Other Income") badgeClass = "badge-other-income";
        else if (tx.transaction_type === "Operating Expense") badgeClass = "badge-operating-expense";
        else if (tx.transaction_type === "Cost of Goods Sold") badgeClass = "badge-cogs";

        const isIncome = ["Revenue", "Other Income"].includes(tx.transaction_type);
        const amtColor = isIncome ? "text-success" : (tx.transaction_type.includes("Expense") || tx.transaction_type === "Cost of Goods Sold" ? "text-danger" : "text-dark");

        return `
            <tr>
                <td class="text-nowrap small text-muted">${formatDate(tx.transaction_date)}</td>
                <td>
                    <div class="fw-semibold text-dark">${tx.description}</div>
                    ${tx.notes ? `<small class="text-muted d-block text-truncate" style="max-width: 250px;">${tx.notes}</small>` : ''}
                    ${tx.is_sample ? '<span class="badge badge-sample">SAMPLE</span>' : ''}
                </td>
                <td>
                    <span class="badge-classification ${badgeClass}">${tx.transaction_type}</span>
                </td>
                <td class="small text-muted">${tx.category_name || "—"}</td>
                <td class="small">
                    <div>${tx.payment_method || "—"}</div>
                    ${tx.reference_number ? `<small class="text-muted text-uppercase">${tx.reference_number}</small>` : ''}
                </td>
                <td class="text-end fw-bold ${amtColor} text-nowrap">
                    ${isIncome ? '+' : '-'}${formatMoney(tx.amount, currency)}
                </td>
                <td class="text-center text-nowrap">
                    <button class="btn btn-sm btn-light py-1 px-2 border" title="Edit" onclick='openEditModal(${JSON.stringify(tx).replace(/'/g, "&#39;")})'>
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-light text-danger py-1 px-2 border ms-1" title="Delete" onclick="deleteTransaction('${tx.id}', '${tx.description.replace(/'/g, "\\'")}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function renderPagination(page, totalPages, total) {
    const ul = document.getElementById("paginationUl");
    const info = document.getElementById("paginationInfo");

    const startIdx = total === 0 ? 0 : (page - 1) * pageSize + 1;
    const endIdx = Math.min(page * pageSize, total);
    info.textContent = `Showing ${startIdx} to ${endIdx} of ${total} records`;

    if (totalPages <= 1) {
        ul.innerHTML = "";
        return;
    }

    let html = `
        <li class="page-item ${page === 1 ? 'disabled' : ''}">
            <a class="page-link" href="javascript:void(0)" onclick="loadTransactions(${page - 1})">Prev</a>
        </li>
    `;

    for (let p = Math.max(1, page - 2); p <= Math.min(totalPages, page + 2); p++) {
        html += `
            <li class="page-item ${p === page ? 'active' : ''}">
                <a class="page-link" href="javascript:void(0)" onclick="loadTransactions(${p})">${p}</a>
            </li>
        `;
    }

    html += `
        <li class="page-item ${page === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="javascript:void(0)" onclick="loadTransactions(${page + 1})">Next</a>
        </li>
    `;

    ul.innerHTML = html;
}

document.getElementById("filterForm").addEventListener("submit", (e) => {
    e.preventDefault();
    loadTransactions(1);
});

function resetFilters() {
    document.getElementById("filterSearch").value = "";
    document.getElementById("filterType").value = "";
    document.getElementById("filterCategory").value = "";
    document.getElementById("filterStartDate").value = "";
    document.getElementById("filterEndDate").value = "";
    loadTransactions(1);
}

function openAddTransactionModal() {
    document.getElementById("modalTitle").textContent = "Add New Transaction";
    document.getElementById("editTxId").value = "";
    document.getElementById("txDescription").value = "";
    document.getElementById("txAmount").value = "";
    document.getElementById("txDate").value = new Date().toISOString().split("T")[0];
    document.getElementById("txType").value = "Operating Expense";
    document.getElementById("txCategory").value = "";
    document.getElementById("txReference").value = "";
    document.getElementById("txNotes").value = "";
    txModalInstance.show();
}

function openEditModal(tx) {
    document.getElementById("modalTitle").textContent = "Edit Transaction";
    document.getElementById("editTxId").value = tx.id;
    document.getElementById("txDescription").value = tx.description;
    document.getElementById("txAmount").value = tx.amount;
    document.getElementById("txDate").value = tx.transaction_date;
    document.getElementById("txType").value = tx.transaction_type;
    document.getElementById("txCategory").value = tx.category_id || "";
    document.getElementById("txPaymentMethod").value = tx.payment_method || "Bank Transfer";
    document.getElementById("txReference").value = tx.reference_number || "";
    document.getElementById("txNotes").value = tx.notes || "";
    txModalInstance.show();
}

document.getElementById("transactionForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("saveTxBtn");
    btn.disabled = true;
    btn.textContent = "Saving...";

    const txId = document.getElementById("editTxId").value;
    const user = API.getCurrentUser() || {};

    const payload = {
        description: document.getElementById("txDescription").value.trim(),
        amount: parseFloat(document.getElementById("txAmount").value),
        transaction_date: document.getElementById("txDate").value,
        transaction_type: document.getElementById("txType").value,
        category_id: document.getElementById("txCategory").value || null,
        payment_method: document.getElementById("txPaymentMethod").value,
        reference_number: document.getElementById("txReference").value.trim() || null,
        notes: document.getElementById("txNotes").value.trim() || null,
        currency: user.default_currency || "INR"
    };

    try {
        if (txId) {
            await API.patch(`/transactions/${txId}`, payload);
            showToast("Transaction updated successfully.", "success");
        } else {
            await API.post("/transactions", payload);
            showToast("Transaction added successfully.", "success");
        }
        txModalInstance.hide();
        loadTransactions(currentPage);
    } catch (err) {
        alert(err.message || "Failed to save transaction.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Save Transaction";
    }
});

async function deleteTransaction(txId, desc) {
    if (confirm(`Are you sure you want to delete '${desc}'? This action cannot be undone.`)) {
        try {
            await API.delete(`/transactions/${txId}`);
            showToast("Transaction deleted.", "info");
            loadTransactions(currentPage);
        } catch (err) {
            showToast(err.message || "Could not delete transaction.", "danger");
        }
    }
}

function exportTransactionsCsv() {
    const user = API.getCurrentUser() || {};
    const query = new URLSearchParams({
        search: document.getElementById("filterSearch").value.trim(),
        transaction_type: document.getElementById("filterType").value,
        category_id: document.getElementById("filterCategory").value,
        start_date: document.getElementById("filterStartDate").value,
        end_date: document.getElementById("filterEndDate").value,
        currency: user.default_currency || "INR"
    }).toString();

    window.location.href = `${API_BASE_URL}/transactions/export/csv?${query}`;
}
