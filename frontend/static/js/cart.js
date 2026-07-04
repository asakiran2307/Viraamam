/**
 * cart.js — Cart drawer, add/remove/update, live total, toast notifications.
 */
const Cart = (() => {
  const overlay = document.getElementById('cart-overlay');
  const drawer  = document.getElementById('cart-drawer');
  const badgeEl = document.getElementById('cart-badge');

  function open() {
    overlay?.classList.add('open');
    drawer?.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    overlay?.classList.remove('open');
    drawer?.classList.remove('open');
    document.body.style.overflow = '';
  }

  function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✓' : '✕'}</span> ${msg}`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  }

  async function fetchCount() {
    try {
      const res = await fetch('/cart/count');
      const data = await res.json();
      updateBadge(data.count || 0);
    } catch (_) {}
  }

  function updateBadge(count) {
    if (!badgeEl) return;
    badgeEl.textContent = count;
    badgeEl.style.display = count > 0 ? 'flex' : 'none';
  }

  async function addItem(itemId, qty = 1) {
    const res = await fetch('/cart/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrf(),
      },
      body: JSON.stringify({ item_id: itemId, qty }),
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'Added to cart!', 'success');
      updateBadge(data.cart_count);
    } else {
      showToast(data.message || 'Failed to add item.', 'danger');
    }
    return data;
  }

  async function updateItem(itemId, qty) {
    await fetch('/cart/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrf(),
      },
      body: JSON.stringify({ item_id: itemId, qty }),
    });
    await refreshDrawer();
  }

  async function removeItem(itemId) {
    await fetch('/cart/remove', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrf(),
      },
      body: JSON.stringify({ item_id: itemId }),
    });
    await refreshDrawer();
    showToast('Item removed.', 'info');
  }

  async function refreshDrawer() {
    const content = document.getElementById('cart-items-content');
    if (!content) return;
    // Reload drawer content from server
    const res = await fetch('/cart/?partial=1', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (res.ok) {
      const html = await res.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const newContent = doc.getElementById('cart-items-content');
      if (newContent) content.innerHTML = newContent.innerHTML;
    }
    await fetchCount();
  }

  function getCsrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // ── Wire up events ───────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    fetchCount();

    // Open cart
    document.querySelectorAll('[data-cart-open]').forEach(el => {
      el.addEventListener('click', open);
    });

    // Close cart
    overlay?.addEventListener('click', close);
    document.querySelectorAll('[data-cart-close]').forEach(el => {
      el.addEventListener('click', close);
    });

    // Add-to-cart buttons on catalog/detail pages
    document.querySelectorAll('[data-add-to-cart]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const itemId = btn.dataset.addToCart;
        const qtyEl = document.getElementById('item-qty');
        const qty = qtyEl ? parseInt(qtyEl.value) : 1;
        btn.disabled = true;
        await addItem(itemId, qty);
        btn.disabled = false;
      });
    });

    // Quantity +/- in drawer
    document.addEventListener('click', async (e) => {
      const target = e.target.closest('[data-qty-change]');
      if (!target) return;
      const itemId = target.dataset.itemId;
      const delta  = parseInt(target.dataset.qtyChange);
      const qtyEl  = document.querySelector(`[data-qty-display="${itemId}"]`);
      if (!qtyEl) return;
      const newQty = Math.max(0, parseInt(qtyEl.textContent) + delta);
      await updateItem(itemId, newQty);
    });

    // Remove from drawer
    document.addEventListener('click', async (e) => {
      const target = e.target.closest('[data-remove-item]');
      if (!target) return;
      const itemId = target.dataset.removeItem;
      await removeItem(itemId);
    });
  });

  return { open, close, addItem, removeItem, showToast, fetchCount };
})();
