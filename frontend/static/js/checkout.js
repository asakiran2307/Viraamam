/**
 * checkout.js — Direct order placement without payment gateway.
 */
document.addEventListener('DOMContentLoaded', () => {
  const checkoutBtn = document.getElementById('checkout-btn');
  if (!checkoutBtn) return;

  checkoutBtn.addEventListener('click', placeOrder);
});

async function placeOrder() {
  const btn = document.getElementById('checkout-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="payment-spinner" style="display:inline-block;width:20px;height:20px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;"></span> Placing Order…';

  try {
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const response = await fetch('/payments/place-order', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrf,
      },
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showSuccess(data.order_id);
    } else {
      showCheckoutError(data.error || 'Failed to place order.');
      resetBtn(btn);
    }
  } catch (err) {
    showCheckoutError('Unexpected error. Please try again.');
    resetBtn(btn);
    console.error(err);
  }
}

function showSuccess(orderId) {
  const panel = document.getElementById('checkout-action-panel');
  if (panel) panel.innerHTML = `
    <div class="payment-success" style="text-align:center; padding: 2rem;">
      <div class="success-icon" style="font-size: 3rem; margin-bottom: 1rem;">✅</div>
      <h3 style="font-family:var(--font-display);color:var(--color-brown-800);margin-bottom:0.5rem;">Order Confirmed!</h3>
      <p style="color:var(--color-brown-600);margin-bottom:1.5rem;">Your order #${orderId} has been successfully placed. We're preparing it right away!</p>
      <a href="/orders/${orderId}" class="btn btn-primary" style="display:inline-block; padding: 0.75rem 1.5rem; background: var(--color-orange); color: white; border-radius: 8px; text-decoration: none; font-weight: 500;">View Order Details</a>
    </div>`;
}

function showCheckoutError(msg) {
  const errorEl = document.getElementById('checkout-error');
  if (errorEl) {
    errorEl.textContent = msg;
    errorEl.style.display = 'block';
    setTimeout(() => { errorEl.style.display = 'none'; }, 6000);
  }
}

function resetBtn(btn) {
  btn.disabled = false;
  btn.innerHTML = 'Place Order Now';
}
