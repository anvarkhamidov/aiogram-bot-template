const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const API_BASE = '';
const headers = {
    'Content-Type': 'application/json',
    'X-Telegram-Init-Data': tg.initData || '',
};

let currentView = 'restaurants';

// --- API helpers ---
async function api(path, options = {}) {
    const resp = await fetch(API_BASE + path, {
        headers,
        ...options,
    });
    return resp.json();
}

// --- Views ---
function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId + '-view').classList.add('active');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const navMap = { restaurants: 'nav-home', cart: 'nav-cart', orders: 'nav-orders', menu: 'nav-home' };
    const navBtn = document.getElementById(navMap[viewId]);
    if (navBtn) navBtn.classList.add('active');
    currentView = viewId;
}

// --- Restaurants ---
async function showRestaurants() {
    showView('restaurants');
    const restaurants = await api('/api/restaurants');
    const list = document.getElementById('restaurants-list');

    if (!restaurants.length) {
        list.innerHTML = '<div class="empty-state"><p>No restaurants available</p></div>';
        return;
    }

    list.innerHTML = restaurants.map(r => `
        <div class="card" onclick="showMenu(${r.id}, '${escapeHtml(r.name)}', '${escapeHtml(r.description || '')}')">
            <div class="card-title">${escapeHtml(r.name)}</div>
            ${r.description ? `<div class="card-subtitle">${escapeHtml(r.description)}</div>` : ''}
            ${r.address ? `<div class="card-subtitle">${escapeHtml(r.address)}</div>` : ''}
        </div>
    `).join('');
}

// --- Menu ---
async function showMenu(restaurantId, name, desc) {
    showView('menu');
    document.getElementById('restaurant-name').textContent = name;
    document.getElementById('restaurant-desc').textContent = desc;

    const categories = await api(`/api/restaurants/${restaurantId}/menu`);
    const list = document.getElementById('menu-list');

    if (!categories.length) {
        list.innerHTML = '<div class="empty-state"><p>Menu is empty</p></div>';
        return;
    }

    let html = '';
    for (const cat of categories) {
        html += `<div class="category-header">${escapeHtml(cat.name)}</div>`;
        for (const p of cat.products) {
            if (!p.is_available) continue;
            html += `
                <div class="card">
                    <div class="card-row">
                        <div>
                            <div class="card-title">${escapeHtml(p.name)}</div>
                            ${p.description ? `<div class="card-subtitle">${escapeHtml(p.description)}</div>` : ''}
                        </div>
                        <button class="btn small" onclick="addToCart(${p.id}); event.stopPropagation();">Add</button>
                    </div>
                    <div class="card-price">${p.price_display} $</div>
                </div>
            `;
        }
    }
    list.innerHTML = html;
}

// --- Cart ---
async function addToCart(productId) {
    await api('/api/cart/add', {
        method: 'POST',
        body: JSON.stringify({ product_id: productId, quantity: 1 }),
    });
    tg.HapticFeedback.impactOccurred('light');
    await updateCartBadge();
}

async function showCart() {
    showView('cart');
    const data = await api('/api/cart');
    const list = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    const formEl = document.getElementById('checkout-form');

    if (!data.items || !data.items.length) {
        list.innerHTML = '<div class="empty-state"><p>Your cart is empty</p></div>';
        totalEl.textContent = '';
        formEl.style.display = 'none';
        return;
    }

    list.innerHTML = data.items.map(item => `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-name">${escapeHtml(item.product_name)}</div>
                <div class="cart-item-detail">x${item.quantity} &middot; ${(item.subtotal / 100).toFixed(2)} $</div>
            </div>
            <button class="btn danger" onclick="removeFromCart(${item.id})">Remove</button>
        </div>
    `).join('');

    totalEl.textContent = `Total: ${(data.total / 100).toFixed(2)} $`;
    formEl.style.display = 'block';
}

async function removeFromCart(itemId) {
    await api(`/api/cart/${itemId}`, { method: 'DELETE' });
    await showCart();
    await updateCartBadge();
}

async function updateCartBadge() {
    try {
        const data = await api('/api/cart');
        const badge = document.getElementById('cart-badge');
        const count = data.items ? data.items.reduce((sum, i) => sum + i.quantity, 0) : 0;
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline' : 'none';
    } catch (e) {
        // ignore auth errors for badge
    }
}

// --- Orders ---
async function placeOrder() {
    const address = document.getElementById('address-input').value.trim();
    const phone = document.getElementById('phone-input').value.trim();
    const comment = document.getElementById('comment-input').value.trim();

    if (!address || !phone) {
        tg.showAlert('Please fill in address and phone number.');
        return;
    }

    const result = await api('/api/orders', {
        method: 'POST',
        body: JSON.stringify({ address, phone, comment: comment || null }),
    });

    if (result.error) {
        tg.showAlert(result.error);
        return;
    }

    tg.HapticFeedback.notificationOccurred('success');
    tg.showAlert(`Order #${result.id} placed successfully!`);
    await updateCartBadge();
    showOrders();
}

async function showOrders() {
    showView('orders');
    const orders = await api('/api/orders');
    const list = document.getElementById('orders-list');

    if (!orders.length) {
        list.innerHTML = '<div class="empty-state"><p>No orders yet</p></div>';
        return;
    }

    list.innerHTML = orders.map(o => `
        <div class="order-card">
            <div class="card-row">
                <div class="card-title">Order #${o.id}</div>
                <span class="order-status status-${o.status}">${o.status}</span>
            </div>
            <div class="card-subtitle" style="margin-top:6px">${o.address}</div>
            <div style="margin-top:8px">
                ${o.items.map(i => `<div class="card-subtitle">${escapeHtml(i.name)} x${i.quantity}</div>`).join('')}
            </div>
            <div class="card-price">${o.total_display} $</div>
        </div>
    `).join('');
}

// --- Helpers ---
function escapeHtml(str) {
    if (!str) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return str.replace(/[&<>"']/g, c => map[c]);
}

// --- Init ---
showRestaurants();
updateCartBadge();
