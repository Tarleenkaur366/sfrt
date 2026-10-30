/**
 * Smart Financial Reporting Tool (SFRT) - CSV Import Controller
 */

let activePreviewData = null;

document.addEventListener("DOMContentLoaded", () => {
    // Set sample CSV button href
    const sampleBtn = document.getElementById("sampleCsvBtn");
    if (sampleBtn) {
        sampleBtn.href = `${API_BASE_URL}/imports/sample-csv`;
    }
    loadImportHistory();
});

async function uploadAndPreview() {
    const fileInput = document.getElementById("csvFileInput");
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a CSV file first.");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    const btn = document.getElementById("uploadPreviewBtn");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Validating...`;

    try {
        const preview = await API.upload("/imports/preview", formData);
        activePreviewData = preview;
        renderPreview(preview);
    } catch (err) {
        alert(err.message || "Failed to parse CSV file.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-eye me-1"></i> Validate & Preview`;
    }
}

function renderPreview(preview) {
    document.getElementById("previewFileName").textContent = `${preview.file_name} (${preview.total_rows} rows detected)`;
    document.getElementById("pTotalRows").textContent = preview.total_rows;
    document.getElementById("pValidRows").textContent = preview.valid_rows_count;
    document.getElementById("pInvalidRows").textContent = preview.invalid_rows_count;
    document.getElementById("pDuplicateRows").textContent = preview.duplicate_rows_count;

    const tbody = document.getElementById("previewTbody");
    tbody.innerHTML = preview.sample_preview.map(row => {
        let statusBadge = "";
        if (!row.is_valid) {
            statusBadge = `<span class="badge bg-danger">Invalid: ${row.validation_errors.join(', ')}</span>`;
        } else if (row.is_duplicate) {
            statusBadge = `<span class="badge bg-warning text-dark">Potential Duplicate</span>`;
        } else {
            statusBadge = `<span class="badge bg-success">Ready</span>`;
        }

        return `
            <tr class="${!row.is_valid ? 'table-danger' : (row.is_duplicate ? 'table-warning' : '')}">
                <td class="text-muted small">${row.row_number}</td>
                <td class="small">${row.transaction_date || '—'}</td>
                <td class="small fw-semibold">${row.description || '—'}</td>
                <td class="small">${row.transaction_type || '—'}</td>
                <td class="small">${row.category || 'General'}</td>
                <td class="small text-end fw-bold">${row.amount !== null ? row.amount.toFixed(2) : '—'}</td>
                <td>${statusBadge}</td>
            </tr>
        `;
    }).join("");

    document.getElementById("previewCard").style.display = "block";
    document.getElementById("previewCard").scrollIntoView({ behavior: "smooth" });
}

function cancelPreview() {
    document.getElementById("previewCard").style.display = "none";
    document.getElementById("csvFileInput").value = "";
    activePreviewData = null;
}

async function confirmImport() {
    if (!activePreviewData || !activePreviewData.all_valid_records) {
        alert("No valid preview data available.");
        return;
    }

    const skipDups = document.getElementById("skipDupsCheck").checked;
    const btn = document.getElementById("confirmImportBtn");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Inserting...`;

    try {
        const payload = {
            file_name: activePreviewData.file_name,
            records: activePreviewData.all_valid_records,
            skip_duplicates: skipDups
        };

        const res = await API.post("/imports/confirm", payload);
        showToast(`Successfully imported ${res.successful_rows} transactions!`, "success");
        cancelPreview();
        loadImportHistory();
    } catch (err) {
        alert(err.message || "Failed to commit import.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-check-circle me-1"></i> Confirm & Insert Records`;
    }
}

async function loadImportHistory() {
    const tbody = document.getElementById("importJobsTbody");
    try {
        const jobs = await API.get("/imports");
        if (!jobs || jobs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No past import jobs found.</td></tr>`;
            return;
        }

        tbody.innerHTML = jobs.map(j => `
            <tr>
                <td class="small text-muted">${formatDate(j.created_at)}</td>
                <td class="fw-semibold">${j.file_name}</td>
                <td>
                    <span class="badge ${j.status === 'COMPLETED' ? 'bg-success' : (j.status === 'FAILED' ? 'bg-danger' : 'bg-warning')}">
                        ${j.status}
                    </span>
                </td>
                <td>${j.total_rows}</td>
                <td class="text-success fw-bold">${j.successful_rows}</td>
                <td class="text-warning">${j.duplicate_rows}</td>
                <td class="text-danger">${j.failed_rows}</td>
            </tr>
        `).join("");
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Failed to load history.</td></tr>`;
    }
}
