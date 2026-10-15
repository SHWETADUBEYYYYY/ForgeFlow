document.addEventListener('DOMContentLoaded', async () => {
    const checkoutItemsContainer = document.getElementById('checkout-items-container');
    const checkoutTotalSpan = document.getElementById('checkout-total');
    const checkoutForm = document.getElementById('checkout-form');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');

    async function fetchCheckoutSummary() {
        try {
            const response = await fetch('/api/cart');
            const data = await response.json();

            if (!response.ok) {
                if (response.status === 401) {
                    checkoutItemsContainer.innerHTML = '<p>Please <a href="/login">log in</a> to proceed to checkout.</p>';
                } else {
                    displayMessage(errorMessage, data.detail || 'Failed to load cart for checkout.', true);
                    checkoutItemsContainer.innerHTML = '<p class="error-message">Failed to load cart items.</p>';
                }
                checkoutForm.style.display = 'none';
                return;
            }

            renderCheckoutSummary(data);
            updateCartCount();
        } catch (error) {
            console.error('Error fetching cart for checkout:', error);
            displayMessage(errorMessage, 'An unexpected error occurred while loading your cart.', true);
            checkoutItemsContainer.innerHTML = '<p class="error-message">Failed to load cart items.</p>';
            checkoutForm.style.display = 'none';
        }
    }

    function renderCheckoutSummary(cart) {
        checkoutItemsContainer.innerHTML = '';
        if (cart.items.length === 0) {
            checkoutItemsContainer.innerHTML = '<p>Your cart is empty. Please add items before checking out.</p>';
            checkoutTotalSpan.textContent = '$0.00';
            checkoutForm.style.display = 'none';
            return;
        }

        let total = 0;
        cart.items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'checkout-item';
            const itemSubtotal = item.product.price * item.quantity;
            total += itemSubtotal;

            itemDiv.innerHTML = `
                <p>${item.product.name} x ${item.quantity} - $${itemSubtotal.toFixed(2)}</p>
            `;
            checkoutItemsContainer.appendChild(itemDiv);
        });

        checkoutTotalSpan.textContent = `$${total.toFixed(2)}`;
        checkoutForm.style.display = 'block';
    }

    checkoutForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        displayMessage(errorMessage, '', false);
        displayMessage(successMessage, '', false);

        const formData = new FormData(checkoutForm);
        const shippingInfo = {
            name: formData.get('name'),
            address: formData.get('address'),
            city: formData.get('city'),
            zip: formData.get('zip')
        };

        try {
            const response = await fetch('/api/orders/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(shippingInfo) // Pass shipping info to backend
            });

            const data = await response.json();

            if (response.ok) {
                displayMessage(successMessage, 'Your simulated order has been placed successfully! Redirecting to orders...', false);
                updateCartCount(); // Clear cart count in header
                setTimeout(() => {
                    window.location.href = '/orders';
                }, 2000);
            } else {
                displayMessage(errorMessage, data.detail || 'Failed to place simulated order.', true);
            }
        } catch (error) {
            console.error('Error during checkout:', error);
            displayMessage(errorMessage, 'An unexpected error occurred during checkout.', true);
        }
    });

    fetchCheckoutSummary();
    updateAuthUI();
    updateCartCount();
});
