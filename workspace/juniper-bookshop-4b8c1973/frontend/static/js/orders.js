document.addEventListener('DOMContentLoaded', async () => {
    const ordersListDiv = document.getElementById('orders-list');
    const errorMessage = document.getElementById('error-message');

    async function fetchOrders() {
        try {
            const response = await fetch('/api/orders');
            const data = await response.json();

            if (!response.ok) {
                if (response.status === 401) {
                    ordersListDiv.innerHTML = '<p>Please <a href="/login">log in</a> to view your orders.</p>';
                } else {
                    displayMessage(errorMessage, data.detail || 'Failed to load orders.', true);
                    ordersListDiv.innerHTML = '<p class="error-message">Failed to load your orders.</p>';
                }
                return;
            }

            renderOrders(data);
        } catch (error) {
            console.error('Error fetching orders:', error);
            displayMessage(errorMessage, 'An unexpected error occurred while loading your orders.', true);
            ordersListDiv.innerHTML = '<p class="error-message">Failed to load your orders.</p>';
        }
    }

    function renderOrders(orders) {
        ordersListDiv.innerHTML = '';
        if (orders.length === 0) {
            ordersListDiv.innerHTML = '<p>You have no past orders.</p>';
            return;
        }

        orders.forEach(order => {
            const orderDiv = document.createElement('div');
            orderDiv.className = 'order-card';

            const orderDate = new Date(order.order_date).toLocaleDateString();
            let totalAmount = 0;
            const itemsHtml = order.items.map(item => {
                const itemTotal = item.price * item.quantity;
                totalAmount += itemTotal;
                return `<li>${item.product_name} x ${item.quantity} - $${itemTotal.toFixed(2)}</li>`;
            }).join('');

            orderDiv.innerHTML = `
                <h3>Order #${order.id}</h3>
                <p>Date: ${orderDate}</p>
                <p>Status: ${order.status}</p>
                <p>Shipping Address: ${order.shipping_address}</p>
                <h4>Items:</h4>
                <ul>${itemsHtml}</ul>
                <p class="order-total">Total: $${totalAmount.toFixed(2)}</p>
            `;
            ordersListDiv.appendChild(orderDiv);
        });
    }

    fetchOrders();
    updateAuthUI();
    updateCartCount();
});
