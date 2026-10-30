/**
 * Smart Financial Reporting Tool (SFRT) - Centralized API & Utility Module
 */

const API_BASE_URL = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
    ? (window.location.port === "8000" ? "/api/v1" : "http://127.0.0.1:8000/api/v1")
    : "/api/v1";

const SFRT_TOKEN_KEY = "sfrt_auth_token";
const SFRT_USER_KEY = "sfrt_user_profile";
const SFRT_PERIOD_KEY = "sfrt_selected_period";

const API = {
    getToken() {
        return localStorage.getItem(SFRT_TOKEN_KEY) || "";
    },

    setSession(token, user) {
        if (token) localStorage.setItem(SFRT_TOKEN_KEY, token);
        if (user) localStorage.setItem(SFRT_USER_KEY, JSON.stringify(user));
    },

    getCurrentUser() {
        const u = localStorage.getItem(SFRT_USER_KEY);
        try {
            return u ? JSON.parse(u) : null;
        } catch (e) {
            return null;
        }
    },

    clearSession() {
        localStorage.removeItem(SFRT_TOKEN_KEY);
        localStorage.removeItem(SFRT_USER_KEY);
    },

    async request(endpoint, options = {}) {
        const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
        const headers = options.headers || {};

        const token = API.getToken();
        if (token && !headers["Authorization"]) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        if (!options.isFormData && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }

        const config = {
            ...options,
            headers,
            credentials: "include" // Send and receive HTTP-only cookies
        };

        try {
            const res = await fetch(url, config);

            if (res.status === 401) {
                // If not on landing or login page, redirect to login
                const currentPath = window.location.pathname;
                if (!currentPath.includes("login.html") && !currentPath.includes("register.html") && !currentPath.endsWith("/") && !currentPath.endsWith("index.html")) {
                    API.clearSession();
                    window.location.href = "login.html?expired=true";
                }
                try {
                    const errJson = await res.json();
                    throw new Error(errJson.detail || "Invalid email or password.");
                } catch (jsonErr) {
                    if (jsonErr.message && !jsonErr.message.includes("Unexpected")) {
                        throw jsonErr;
                    }
                    throw new Error("Authentication required or session expired.");
                }
            }

            if (res.status === 204) {
                return null;
            }

            const contentType = res.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const data = await res.json();
                if (!res.ok) {
                    const errorMsg = data.detail || data.message || "An unexpected error occurred.";
                    throw new Error(errorMsg);
                }
                return data;
            } else if (contentType.includes("text/csv") || contentType.includes("application/pdf")) {
                if (!res.ok) throw new Error("File download failed.");
                return res.blob();
            } else {
                if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
                return res.text();
            }
        } catch (error) {
            console.error(`API Error on [${options.method || "GET"} ${endpoint}]:`, error);
            throw error;
        }
    },

    get(endpoint, params = {}) {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null && v !== "") {
                query.append(k, v);
            }
        });
        const qs = query.toString();
        const url = qs ? `${endpoint}?${qs}` : endpoint;
        return API.request(url, { method: "GET" });
    },

    post(endpoint, body = {}) {
        return API.request(endpoint, {
            method: "POST",
            body: JSON.stringify(body)
        });
    },

    patch(endpoint, body = {}) {
        return API.request(endpoint, {
            method: "PATCH",
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return API.request(endpoint, { method: "DELETE" });
    },

    upload(endpoint, formData) {
        return API.request(endpoint, {
            method: "POST",
            body: formData,
            isFormData: true
        });
    }
};

// UI Toast helper
function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }

    const toastId = "toast-" + Date.now();
    const bgClass = type === "success" ? "bg-success text-white" :
                    type === "danger" || type === "error" ? "bg-danger text-white" :
                    type === "warning" ? "bg-warning text-dark" : "bg-primary text-white";

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center ${bgClass} border-0 show shadow-lg mb-2`;
    toastEl.id = toastId;
    toastEl.setAttribute("role", "alert");
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-medium py-2 px-3">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
        </div>
    `;
    container.appendChild(toastEl);
    setTimeout(() => {
        if (toastEl.parentNode) toastEl.remove();
    }, 4500);
}

// Formatting helpers
function formatMoney(amount, currency = "INR") {
    if (amount === null || amount === undefined || isNaN(amount)) return "—";
    const num = Number(amount);
    try {
        if (currency === "INR") {
            return "₹" + num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        } else {
            return num.toLocaleString("en-US", { style: "currency", currency: currency });
        }
    } catch (e) {
        return `${currency} ${num.toFixed(2)}`;
    }
}

function formatDate(dateStr) {
    if (!dateStr) return "—";
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
    } catch (e) {
        return dateStr;
    }
}

function formatPct(val) {
    if (val === null || val === undefined || isNaN(val)) return "N/A";
    const num = Number(val);
    const prefix = num > 0 ? "+" : "";
    return `${prefix}${num.toFixed(1)}%`;
}

function getStoredPeriod() {
    const today = new Date();
    const curYear = today.getFullYear();
    const defStart = `${curYear}-01-01`;
    const defEnd = today.toISOString().split("T")[0];

    const stored = localStorage.getItem(SFRT_PERIOD_KEY);
    if (stored) {
        try {
            return JSON.parse(stored);
        } catch (e) {}
    }
    return { start_date: defStart, end_date: defEnd, label: "Year to Date" };
}

function setStoredPeriod(start_date, end_date, label = "Custom Range") {
    localStorage.setItem(SFRT_PERIOD_KEY, JSON.stringify({ start_date, end_date, label }));
}
