/**
 * admin.js — Admin panel JS: image preview on upload, toggle switches, GSAP reveal.
 */
document.addEventListener('DOMContentLoaded', () => {
  initImagePreviews();
  initToggleSwitches();
  initTableSearch();
  initMobileNav();
  initGsapReveal();
});

// ── Image Upload Preview ──────────────────────────────────────────────────
function initImagePreviews() {
  document.querySelectorAll('input[type="file"][data-preview]').forEach(input => {
    const previewId = input.dataset.preview;
    const preview = document.getElementById(previewId);
    if (!preview) return;
    input.addEventListener('change', () => {
      const file = input.files[0];
      if (!file) return;
      // Validate client-side (server re-validates)
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file.');
        input.value = '';
        return;
      }
      const reader = new FileReader();
      reader.onload = e => {
        preview.src = e.target.result;
        preview.classList.add('visible');
      };
      reader.readAsDataURL(file);
    });
  });

  // Upload placeholder click
  document.querySelectorAll('.upload-placeholder').forEach(ph => {
    ph.addEventListener('click', () => {
      const input = document.querySelector(`#${ph.dataset.for}`);
      input?.click();
    });
  });
}

// ── Toggle Switches ───────────────────────────────────────────────────────
function initToggleSwitches() {
  document.querySelectorAll('[data-toggle-url]').forEach(toggle => {
    const track = toggle.querySelector('.toggle-track');
    toggle.addEventListener('click', async () => {
      const url = toggle.dataset.toggleUrl;
      const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf },
      });
      const data = await res.json();
      if (data.success) {
        track?.classList.toggle('on', data.is_active);
        showAdminToast(data.is_active ? 'Activated' : 'Deactivated', 'success');
      }
    });
  });
}

// ── Table Search Filter ───────────────────────────────────────────────────
function initTableSearch() {
  const searchInputs = document.querySelectorAll('[data-table-filter]');
  searchInputs.forEach(input => {
    const tableId = input.dataset.tableFilter;
    const table = document.getElementById(tableId);
    if (!table) return;
    input.addEventListener('input', () => {
      const q = input.value.toLowerCase();
      table.querySelectorAll('tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  });
}

// ── Mobile Sidebar Nav ────────────────────────────────────────────────────
function initMobileNav() {
  const sidebar = document.getElementById('admin-sidebar');
  const toggler = document.getElementById('sidebar-toggler');
  const overlay = document.getElementById('sidebar-overlay');

  function showOverlay() {
    if (!overlay) return;
    overlay.style.opacity = '1';
    overlay.style.pointerEvents = 'auto';
  }
  function hideOverlay() {
    if (!overlay) return;
    overlay.style.opacity = '0';
    overlay.style.pointerEvents = 'none';
  }

  toggler?.addEventListener('click', () => {
    const isOpen = sidebar?.classList.toggle('mobile-open');
    if (isOpen) showOverlay(); else hideOverlay();
  });
  overlay?.addEventListener('click', () => {
    sidebar?.classList.remove('mobile-open');
    hideOverlay();
  });
}


// ── Admin Toast Notifications ─────────────────────────────────────────────
function showAdminToast(msg, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : '✕'}</span> ${msg}`;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 400); }, 3000);
}

// ── GSAP Entrance Animations (admin — subtle only) ────────────────────────
function initGsapReveal() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (typeof gsap === 'undefined') return;

  gsap.from('.metric-card', {
    opacity: 0, y: 20, duration: 0.5, stagger: 0.08, ease: 'power2.out',
  });
  gsap.from('.admin-card', {
    opacity: 0, y: 15, duration: 0.5, delay: 0.2, ease: 'power2.out',
  });
}

// ── Confirm Deletes ───────────────────────────────────────────────────────
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', e => {
    const msg = form.dataset.confirm || 'Are you sure?';
    if (!confirm(msg)) e.preventDefault();
  });
});
