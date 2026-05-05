/* ================================================
   TAZARA AI System — Shared JavaScript Utilities
   ================================================ */

const API_BASE = 'http://127.0.0.1:8000';

// ── API Helper ──
async function fetchAPI(path, options = {}) {
    try {
        const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
        
        // Add authentication token
        const token = localStorage.getItem('access_token');
        if (token) {
            options.headers = {
                'Authorization': `Bearer ${token}`,
                ...options.headers
            };
        }
        
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        });
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`fetchAPI(${path}):`, error);
        throw error;
    }
}

async function postAPI(path, body, isFormData = false) {
    const options = {
        method: 'POST',
    };
    
    // Add authentication token
    const token = localStorage.getItem('access_token');
    if (token) {
        options.headers = {
            'Authorization': `Bearer ${token}`
        };
    }
    
    if (isFormData) {
        options.body = body;
        // Don't set Content-Type for FormData (browser sets it automatically with boundary)
    } else {
        options.body = JSON.stringify(body);
        options.headers['Content-Type'] = 'application/json';
    }
    
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    const response = await fetch(url, options);
    if (!response.ok) {
        let errorMsg = `Error ${response.status}`;
        try {
            const errData = await response.json();
            errorMsg = errData.detail || errorMsg;
        } catch {
            errorMsg = await response.text() || errorMsg;
        }
        throw new Error(errorMsg);
    }
    return await response.json();
}

// ── System Status ──
async function checkSystemHealth() {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    if (!dot || !text) return false;

    try {
        const data = await fetchAPI('/health/');
        dot.classList.remove('offline');
        dot.classList.add('online');
        text.textContent = 'System Online';
        text.closest('.status-badge').classList.remove('offline');
        text.closest('.status-badge').classList.add('online');
        return true;
    } catch {
        dot.classList.remove('online');
        dot.classList.add('offline');
        text.textContent = 'System Offline';
        text.closest('.status-badge').classList.remove('online');
        text.closest('.status-badge').classList.add('offline');
        return false;
    }
}

// ── Tab Navigation ──
function initTabs(containerSelector = '.tabs') {
    document.querySelectorAll(containerSelector).forEach(tabBar => {
        const buttons = tabBar.querySelectorAll('.tab-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.tab;
                // Deactivate all
                buttons.forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
                // Activate clicked
                btn.classList.add('active');
                const panel = document.getElementById(target);
                if (panel) panel.classList.add('active');
            });
        });
    });
}

// ── Number Formatting ──
function formatNumber(n, decimals = 0) {
    if (n == null || isNaN(n)) return '—';
    return Number(n).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatCurrency(n) {
    if (n == null || isNaN(n)) return '—';
    const val = Number(n);
    const sign = val < 0 ? '-' : '';
    return `${sign}ZMW ${Math.abs(val).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}


function formatPercent(n, decimals = 1) {
    if (n == null || isNaN(n)) return '—';
    return Number(n).toFixed(decimals) + '%';
}

// ── Chart.js Defaults ──
function setChartDefaults() {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.color = '#a0aec0';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(26, 29, 46, 0.95)';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.1)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
}

// ── Gradient Maker for Chart.js ──
function createGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}

// ── Toast Notifications ──
function showToast(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; z-index: 9999;
        min-width: 300px; max-width: 480px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        animation: slideIn 0.3s ease;
    `;
    const icons = { success: '✅', warning: '⚠️', danger: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ── Loading State ──
function showLoading(container) {
    if (typeof container === 'string') container = document.getElementById(container);
    if (!container) return;
    container.innerHTML = `
        <div class="loading-overlay">
            <div class="spinner"></div>
            <p>Loading data...</p>
        </div>
    `;
}

function showEmpty(container, message = 'No data available', icon = '📭') {
    if (typeof container === 'string') container = document.getElementById(container);
    if (!container) return;
    container.innerHTML = `
        <div class="empty-state">
            <div class="icon">${icon}</div>
            <h3>${message}</h3>
            <p>Check that the API server is running and try again.</p>
        </div>
    `;
}

function showError(container, error) {
    if (typeof container === 'string') container = document.getElementById(container);
    if (!container) return;
    container.innerHTML = `
        <div class="alert alert-danger">
            <span>❌</span>
            <div>
                <strong>Error loading data</strong><br>
                ${error.message || error}
            </div>
        </div>
    `;
}

// ── Sidebar Active Link ──
function setActiveNav() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href') || '';
        if (href === currentPage || (currentPage === '' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
}

// ── Mobile Sidebar Toggle ──
function initMobileSidebar() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    }
}

// ── Initialize Common Components ──
document.addEventListener('DOMContentLoaded', () => {
    setChartDefaults();
    setActiveNav();
    initTabs();
    initMobileSidebar();
    checkSystemHealth();
    initAlertPolling();
});

// ── Alert Polling ──
let lastAlertCount = 0;
function initAlertPolling() {
    setInterval(async () => {
        try {
            const summary = await fetchAPI('/alerts/summary');
            const total = summary.total_unacknowledged || 0;
            
            if (total > lastAlertCount) {
                // New alert!
                const alerts = await fetchAPI('/alerts/?acknowledged=false');
                if (alerts.length > 0) {
                    const latest = alerts[0];
                    const severityMap = { critical: 'danger', warning: 'warning', info: 'info' };
                    showToast(latest.message, severityMap[latest.severity] || 'info');
                }
            }
            lastAlertCount = total;
            
            // Update UI badge if it exists
            const badge = document.getElementById('alertBadge');
            if (badge) {
                badge.textContent = total;
                badge.style.display = total > 0 ? 'inline-block' : 'none';
            }
        } catch (err) {
            console.warn('Alert polling failed:', err);
        }
    }, 15000); // Check every 15 seconds
}

// CSS animation for toasts
const toastStyle = document.createElement('style');
toastStyle.textContent = `
    @keyframes slideIn { from { transform: translateX(100px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes fadeOut { to { opacity: 0; transform: translateY(10px); } }
`;
document.head.appendChild(toastStyle);
