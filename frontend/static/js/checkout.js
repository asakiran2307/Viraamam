/**
 * checkout.js — Razorpay checkout integration.
 * Creates order on server, opens Razorpay widget, verifies payment server-side.
 */
document.addEventListener('DOMContentLoaded', () => {
  const checkoutBtn = document.getElementById('checkout-btn');
  if (!checkoutBtn) return;

  checkoutBtn.addEventListener('click', startCheckout);
});

async function startCheckout() {
  const btn = document.getElementById('checkout-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="payment-spinner" style="display:inline-block;width:20px;height:20px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;"></span> Creating order…';

  try {
    // Step 1: Create order on server (server computes total from DB, not client)
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const orderRes = await fetch('/payments/create-order', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrf,
      },
    });
    const orderData = await orderRes.json();
    if (!orderRes.ok) {
      showCheckoutError(orderData.error || 'Failed to create order.');
      resetBtn(btn);
      return;
    }

    // Step 2: Open Razorpay checkout widget
    const options = {
      key: orderData.key,
      amount: orderData.amount,
      currency: orderData.currency,
      name: 'Viraamam Cafe',
      description: 'Your cafe order',
      order_id: orderData.order_id,
      theme: { color: '#D4622A' },
      handler: async function (response) {
        showVerifying();
        // Step 3: Verify payment signature server-side
        const verifyRes = await fetch('/payments/verify', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf,
          },
          body: JSON.stringify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          }),
        });
        const verifyData = await verifyRes.json();
        if (verifyData.success) {
          showSuccess(verifyData.order_id);
        } else {
          showCheckoutError('Payment verification failed. Please contact support.');
        }
      },
      modal: {
        ondismiss: () => {
          resetBtn(btn);
          showCheckoutError('Payment cancelled.');
        },
      },
    };

    if (typeof Razorpay === 'undefined') {
      // Dynamically load Razorpay script if not yet loaded
      await loadScript('https://checkout.razorpay.com/v1/checkout.js');
    }
    const rzp = new Razorpay(options);
    rzp.on('payment.failed', (resp) => {
      showCheckoutError(`Payment failed: ${resp.error.description}`);
      resetBtn(btn);
    });
    rzp.open();

  } catch (err) {
    showCheckoutError('Unexpected error. Please try again.');
    resetBtn(btn);
    console.error(err);
  }
}

function showVerifying() {
  const panel = document.getElementById('checkout-action-panel');
  if (panel) panel.innerHTML = `
    <div class="payment-verify">
      <div class="payment-spinner"></div>
      <p>Verifying payment…</p>
      <small>Please don't close this page.</small>
    </div>`;
}

function showSuccess(orderId) {
  const panel = document.getElementById('checkout-action-panel');
  if (panel) panel.innerHTML = `
    <div class="payment-success">
      <div class="success-icon">✅</div>
      <h3 style="font-family:var(--font-display);color:var(--color-brown-800);margin-bottom:0.5rem;">Order Confirmed!</h3>
      <p style="color:var(--color-brown-600);margin-bottom:1.5rem;">Your order #${orderId} is confirmed. We'll start preparing it right away!</p>
      <a href="/orders/${orderId}" class="btn btn-primary">View Order</a>
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
  btn.innerHTML = '🔒 Pay Securely';
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}
