/**
 * Smart Financial Reporting Tool (SFRT) - Dynamic App Layout & Navigation Injector
 */

document.addEventListener("DOMContentLoaded", async () => {
    // Check authentication
    const user = API.getCurrentUser();
    const token = API.getToken();

    const path = window.location.pathname;
    const isPublicPage = path.endsWith("/") || path.endsWith("index.html") || path.endsWith("login.html") || path.endsWith("register.html");

    if (!isPublicPage && (!token || !user)) {
        window.location.href = "login.html";
        return;
    }

    if (!isPublicPage) {
        injectAppLayout(user);
    }
});

function injectAppLayout(user) {
    const activeFile = window.location.pathname.split("/").pop() || "dashboard.html";

    // 1. Render Sidebar
    const sidebarHtml = `
    <aside class="sidebar" id="appSidebar">
        <a href="dashboard.html" class="sidebar-brand">
            <i class="bi bi-graph-up-arrow"></i>
            <div>
                <span class="d-block lh-1">SmartFRT</span>
                <small class="text-muted fw-normal" style="font-size: 0.65rem; letter-spacing: 0.05em;">FINANCIAL INTELLIGENCE</small>
            </div>
        </a>

        <div class="sidebar-nav">
            <div class="nav-section-title">Overview</div>
            <a href="dashboard.html" class="sidebar-link ${activeFile === "dashboard.html" ? "active" : ""}">
                <i class="bi bi-speedometer2"></i> Dashboard
            </a>
            <a href="analytics.html" class="sidebar-link ${activeFile === "analytics.html" ? "active" : ""}">
                <i class="bi bi-pie-chart"></i> Analytics
            </a>
            <a href="insights.html" class="sidebar-link ${activeFile === "insights.html" ? "active" : ""}">
                <i class="bi bi-lightbulb"></i> Financial Insights
            </a>

            <div class="nav-section-title mt-3">Bookkeeping</div>
            <a href="transactions.html" class="sidebar-link ${activeFile === "transactions.html" ? "active" : ""}">
                <i class="bi bi-receipt-cutoff"></i> Transactions
            </a>
            <a href="income.html" class="sidebar-link ${activeFile === "income.html" ? "active" : ""}">
                <i class="bi bi-arrow-down-left-circle"></i> Income
            </a>
            <a href="expenses.html" class="sidebar-link ${activeFile === "expenses.html" ? "active" : ""}">
                <i class="bi bi-arrow-up-right-circle"></i> Expenses
            </a>
            <a href="imports.html" class="sidebar-link ${activeFile === "imports.html" ? "active" : ""}">
                <i class="bi bi-file-earmark-arrow-up"></i> Import Data
            </a>

            <div class="nav-section-title mt-3">Reporting</div>
            <a href="reports.html" class="sidebar-link ${activeFile === "reports.html" ? "active" : ""}">
                <i class="bi bi-file-earmark-bar-graph"></i> Financial Reports
            </a>
            <a href="report_history.html" class="sidebar-link ${activeFile === "report_history.html" ? "active" : ""}">
                <i class="bi bi-clock-history"></i> Report History
            </a>

            <div class="nav-section-title mt-3">System</div>
            <a href="settings.html" class="sidebar-link ${activeFile === "settings.html" ? "active" : ""}">
                <i class="bi bi-gear"></i> Settings
            </a>
        </div>

        <div class="sidebar-footer">
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center gap-2 overflow-hidden">
                    <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center fw-bold" style="width: 34px; height: 34px; font-size: 0.85rem;">
                        ${(user.full_name || "U").charAt(0).toUpperCase()}
                    </div>
                    <div class="text-truncate">
                        <div class="fw-semibold text-truncate" style="font-size: 0.85rem;">${user.full_name || "User"}</div>
                        <small class="text-muted d-block text-truncate" style="font-size: 0.75rem;">${user.business_name || user.email}</small>
                    </div>
                </div>
                <button class="btn btn-sm btn-light text-danger border-0" onclick="handleLogout()" title="Logout">
                    <i class="bi bi-box-arrow-right fs-6"></i>
                </button>
            </div>
        </div>
    </aside>
    `;

    // 2. Render Topbar
    const period = getStoredPeriod();
    const topbarHtml = `
    <header class="topbar">
        <div class="d-flex align-items-center gap-3">
            <button class="btn btn-light d-lg-none border" type="button" onclick="toggleSidebar()">
                <i class="bi bi-list fs-5"></i>
            </button>
            <div id="topbarPageTitle">
                <!-- Page specific title injected dynamically -->
            </div>
        </div>

        <div class="d-flex align-items-center gap-3">
            <!-- Global Period Selector -->
            <div class="dropdown d-none d-md-block">
                <button class="btn btn-sm btn-outline-custom dropdown-toggle d-flex align-items-center gap-2" type="button" id="periodDropdownBtn" data-bs-toggle="dropdown">
                    <i class="bi bi-calendar3 text-primary"></i>
                    <span id="periodLabelText">${period.label || "Reporting Period"}</span>
                </button>
                <ul class="dropdown-menu dropdown-menu-end shadow-sm" style="font-size: 0.875rem;">
                    <li><h6 class="dropdown-header">Preset Reporting Periods</h6></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="applyPeriodPreset('ytd')">Year to Date (YTD)</a></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="applyPeriodPreset('this_month')">This Month</a></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="applyPeriodPreset('last_month')">Last Month</a></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="applyPeriodPreset('last_90')">Last 90 Days</a></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="applyPeriodPreset('all')">All Time</a></li>
                </ul>
            </div>

            <!-- Currency Indicator Badge -->
            <div class="badge bg-light text-dark border px-2 py-1 fs-6 d-flex align-items-center gap-1">
                <span class="text-muted" style="font-size: 0.75rem;">CURRENCY:</span>
                <span class="fw-bold text-primary">${user.default_currency || "INR"}</span>
            </div>

            <!-- User Menu -->
            <div class="dropdown">
                <button class="btn btn-sm btn-light border-0 d-flex align-items-center gap-2" type="button" data-bs-toggle="dropdown">
                    <div class="rounded-circle bg-primary-light text-primary d-flex align-items-center justify-content-center fw-bold" style="width: 32px; height: 32px;">
                        ${(user.full_name || "U").charAt(0).toUpperCase()}
                    </div>
                </button>
                <ul class="dropdown-menu dropdown-menu-end shadow-sm" style="font-size: 0.875rem;">
                    <li class="px-3 py-2 border-bottom">
                        <div class="fw-bold">${user.full_name}</div>
                        <small class="text-muted">${user.email}</small>
                    </li>
                    <li><a class="dropdown-item py-2" href="settings.html"><i class="bi bi-person me-2"></i> Profile & Settings</a></li>
                    <li><a class="dropdown-item py-2" href="report_history.html"><i class="bi bi-clock-history me-2"></i> Report Archive</a></li>
                    <li><hr class="dropdown-divider my-1"></li>
                    <li><a class="dropdown-item py-2 text-danger" href="javascript:void(0)" onclick="handleLogout()"><i class="bi bi-box-arrow-right me-2"></i> Logout</a></li>
                </ul>
            </div>
        </div>
    </header>
    `;

    // Inject into DOM
    const sidebarContainer = document.getElementById("sidebarContainer");
    if (sidebarContainer) sidebarContainer.innerHTML = sidebarHtml;

    const topbarContainer = document.getElementById("topbarContainer");
    if (topbarContainer) topbarContainer.innerHTML = topbarHtml;
}

function toggleSidebar() {
    const s = document.getElementById("appSidebar");
    if (s) s.classList.toggle("show");
}

function applyPeriodPreset(preset) {
    const today = new Date();
    const curYear = today.getFullYear();
    const curMonth = today.getMonth(); // 0-indexed
    let start, end, label;

    if (preset === "this_month") {
        start = new Date(curYear, curMonth, 1).toISOString().split("T")[0];
        end = today.toISOString().split("T")[0];
        label = "This Month";
    } else if (preset === "last_month") {
        const lastMonthEnd = new Date(curYear, curMonth, 0);
        const lastMonthStart = new Date(curYear, curMonth - 1, 1);
        start = lastMonthStart.toISOString().split("T")[0];
        end = lastMonthEnd.toISOString().split("T")[0];
        label = "Last Month";
    } else if (preset === "last_90") {
        const past = new Date(today);
        past.setDate(past.getDate() - 90);
        start = past.toISOString().split("T")[0];
        end = today.toISOString().split("T")[0];
        label = "Last 90 Days";
    } else if (preset === "all") {
        start = "2020-01-01";
        end = today.toISOString().split("T")[0];
        label = "All Time";
    } else { // ytd
        start = `${curYear}-01-01`;
        end = today.toISOString().split("T")[0];
        label = "Year to Date (YTD)";
    }

    setStoredPeriod(start, end, label);
    const labelEl = document.getElementById("periodLabelText");
    if (labelEl) labelEl.textContent = label;

    showToast(`Reporting period set to ${label}`, "info");
    if (typeof loadPageData === "function") {
        loadPageData();
    } else {
        window.location.reload();
    }
}

async function handleLogout() {
    if (confirm("Are you sure you want to sign out?")) {
        try {
            await API.post("/auth/logout");
        } catch (e) {
            console.warn("Logout error:", e);
        }
        API.clearSession();
        window.location.href = "login.html";
    }
}
