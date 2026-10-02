/* =============================================
   Job Tracker — Client Application Logic
   ============================================= */

const API = '/api';
let allApplications = [];

// DOM References
const $ = (sel) => document.querySelector(sel);
const tableBody    = $('#tableBody');
const emptyState   = $('#emptyState');
const noResults    = $('#noResults');
const tableWrapper = $('.table-container');
const searchInput  = $('#searchInput');
const statusFilter = $('#statusFilter');
const sortFilter   = $('#sortFilter');
const modalOverlay = $('#modalOverlay');
const deleteOverlay = $('#deleteOverlay');
const appForm      = $('#appForm');
const toastContainer = $('#toastContainer');
const themeToggle  = $('#themeToggle');
const themeIcon    = $('#themeIcon');

// --- Icons (SVGs) ---
const ICONS = {
    moon: `<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>`,
    sun: `<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>`,
    edit: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>`,
    trash: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>`
};

// --- Theme Management ---
function updateThemeIcon(isDark) {
    if (themeIcon) {
        themeIcon.innerHTML = isDark ? ICONS.sun : ICONS.moon;
    }
}

(function initTheme() {
    const saved = localStorage.getItem('jt-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = saved === 'dark' || (!saved && prefersDark);

    if (isDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    updateThemeIcon(isDark);
})();

themeToggle.addEventListener('click', () => {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    const nextDark = !isDark;

    html.setAttribute('data-theme', nextDark ? 'dark' : 'light');
    localStorage.setItem('jt-theme', nextDark ? 'dark' : 'light');
    updateThemeIcon(nextDark);
});

// --- API Client ---
async function apiFetch(path, options = {}) {
    try {
        const res = await fetch(`${API}${path}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (res.status === 204) return null;
        const data = await res.json();
        if (!res.ok) {
            const msg = data.errors ? data.errors.join(', ') : data.error || 'Request failed';
            throw new Error(msg);
        }
        return data;
    } catch (err) {
        if (err.message === 'Failed to fetch') {
            throw new Error('Unable to connect to the server');
        }
        throw err;
    }
}

// --- Data Operations ---
async function loadApplications() {
    allApplications = await apiFetch('/applications');
    renderTable();
    loadStats();
}

async function loadStats() {
    const stats = await apiFetch('/stats');
    $('#statTotal').textContent = stats.total;
    $('#statApplied').textContent = stats.by_status.applied;
    $('#statInterview').textContent = stats.by_status.interview;
    $('#statOffer').textContent = stats.by_status.offer;
}

// --- View Rendering ---
function renderTable() {
    const filtered = getFilteredApps();
    tableBody.innerHTML = '';

    if (allApplications.length === 0) {
        tableWrapper.style.display = 'none';
        noResults.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    if (filtered.length === 0) {
        tableWrapper.style.display = 'none';
        emptyState.style.display = 'none';
        noResults.style.display = 'block';
        return;
    }

    tableWrapper.style.display = 'block';
    emptyState.style.display = 'none';
    noResults.style.display = 'none';

    filtered.forEach((app) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="company-name">${escapeHtml(app.company)}</td>
            <td>${escapeHtml(app.role)}</td>
            <td><span class="badge ${app.status}">${capitalize(app.status)}</span></td>
            <td>${formatDate(app.applied_on)}</td>
            <td class="notes-preview" title="${escapeHtml(app.notes || '')}">${escapeHtml(app.notes || '—')}</td>
            <td>${app.link ? `<a href="${escapeHtml(app.link)}" target="_blank" rel="noopener noreferrer">Visit</a>` : '—'}</td>
            <td class="text-right">
                <div class="action-btn-group">
                    <button class="icon-btn" title="Edit" onclick="openEdit(${app.id})">${ICONS.edit}</button>
                    <button class="icon-btn" title="Delete" onclick="openDelete(${app.id}, '${escapeHtml(app.company)}')">${ICONS.trash}</button>
                </div>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

function getFilteredApps() {
    let apps = [...allApplications];
    const search = searchInput.value.toLowerCase().trim();
    const status = statusFilter.value;
    const sort = sortFilter.value;

    if (search) {
        apps = apps.filter(a =>
            a.company.toLowerCase().includes(search) ||
            a.role.toLowerCase().includes(search) ||
            (a.notes && a.notes.toLowerCase().includes(search))
        );
    }

    if (status) {
        apps = apps.filter(a => a.status === status);
    }

    switch (sort) {
        case 'oldest':
            apps.sort((a, b) => a.applied_on.localeCompare(b.applied_on) || a.id - b.id);
            break;
        case 'company':
            apps.sort((a, b) => a.company.localeCompare(b.company));
            break;
        default: // newest
            apps.sort((a, b) => b.applied_on.localeCompare(a.applied_on) || b.id - a.id);
    }
    return apps;
}

// --- Modals: Add / Edit ---
$('#addBtn').addEventListener('click', () => openModal());

function openModal(app = null) {
    appForm.reset();
    $('#editId').value = '';
    $('#companyError').textContent = '';
    $('#roleError').textContent = '';
    $('#company').classList.remove('error');
    $('#role').classList.remove('error');

    if (app) {
        $('#modalTitle').textContent = 'Edit Application';
        $('#submitBtn').textContent = 'Save Changes';
        $('#editId').value = app.id;
        $('#company').value = app.company;
        $('#role').value = app.role;
        $('#status').value = app.status;
        $('#appliedOn').value = app.applied_on;
        $('#notes').value = app.notes || '';
        $('#link').value = app.link || '';
    } else {
        $('#modalTitle').textContent = 'New Application';
        $('#submitBtn').textContent = 'Save Application';
        $('#appliedOn').value = new Date().toISOString().slice(0, 10);
    }
    modalOverlay.classList.add('active');
    setTimeout(() => $('#company').focus(), 50);
}

function openEdit(id) {
    const app = allApplications.find(a => a.id === id);
    if (app) openModal(app);
}

function closeModal() {
    modalOverlay.classList.remove('active');
}

$('#modalClose').addEventListener('click', closeModal);
$('#cancelBtn').addEventListener('click', closeModal);
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
});

appForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    let valid = true;
    const company = $('#company').value.trim();
    const role = $('#role').value.trim();

    if (!company) {
        $('#companyError').textContent = 'Company is required';
        $('#company').classList.add('error');
        valid = false;
    } else {
        $('#companyError').textContent = '';
        $('#company').classList.remove('error');
    }

    if (!role) {
        $('#roleError').textContent = 'Role is required';
        $('#role').classList.add('error');
        valid = false;
    } else {
        $('#roleError').textContent = '';
        $('#role').classList.remove('error');
    }

    if (!valid) return;

    const payload = {
        company,
        role,
        status: $('#status').value,
        applied_on: $('#appliedOn').value || new Date().toISOString().slice(0, 10),
        notes: $('#notes').value.trim(),
        link: $('#link').value.trim(),
    };

    const editId = $('#editId').value;

    try {
        $('#submitBtn').disabled = true;

        if (editId) {
            await apiFetch(`/applications/${editId}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });
            showToast('Application updated');
        } else {
            await apiFetch('/applications', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            showToast('Application created');
        }

        closeModal();
        await loadApplications();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        $('#submitBtn').disabled = false;
    }
});

// --- Modal: Delete ---
let deleteId = null;

function openDelete(id, company) {
    deleteId = id;
    $('#deleteTarget').textContent = company;
    deleteOverlay.classList.add('active');
}

function closeDelete() {
    deleteOverlay.classList.remove('active');
    deleteId = null;
}

$('#deleteClose').addEventListener('click', closeDelete);
$('#deleteCancelBtn').addEventListener('click', closeDelete);
deleteOverlay.addEventListener('click', (e) => {
    if (e.target === deleteOverlay) closeDelete();
});

$('#deleteConfirmBtn').addEventListener('click', async () => {
    if (!deleteId) return;
    try {
        $('#deleteConfirmBtn').disabled = true;
        await apiFetch(`/applications/${deleteId}`, { method: 'DELETE' });
        showToast('Application removed');
        closeDelete();
        await loadApplications();
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        $('#deleteConfirmBtn').disabled = false;
    }
});

// --- Search & Filters ---
searchInput.addEventListener('input', () => renderTable());
statusFilter.addEventListener('change', () => renderTable());
sortFilter.addEventListener('change', () => renderTable());

// --- Shortcuts ---
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
        closeDelete();
    }
});

// --- Helpers ---
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
        const d = new Date(dateStr + 'T00:00:00');
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

function showToast(message, type = 'default') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.2s ease';
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}

// Initial Load
loadApplications();
