document.addEventListener('DOMContentLoaded', async () => {
    const cartItemsContainer = document.getElementById('cart-items-container');
    const cartTotalSpan = document.getElementById('cart-total');
    const cartSummaryDiv = document.getElementById('cart-summary');
    const checkoutButton = document.getElementById('checkout-button');
    const errorMessage = document.getElementById('error-message');

    async function fetchCart() {
        try {
            const response = await fetch('/api/cart');
            const data = await response.json();

            if (!response.ok) {
                if (response.status === 401) {
                    cartItemsContainer.innerHTML = '<p>Please <a href="/login">log in</a> to view your cart.</p>';
                    cartSummaryDiv.style.display = 'none';
                } else {
                    displayMessage(errorMessage, data.detail || 'Failed to load cart.', true);
                    cartItemsContainer.innerHTML = '<p class="error-message">Failed to load cart items.</p>';
                    cartSummaryDiv.style.display = 'none';
                }
                return;
            }

            renderCart(data);
            updateCartCount();
        } catch (error) {
            console.error('Error fetching cart:', error);
            displayMessage(errorMessage, 'An unexpected error occurred while loading your cart.', true);
            cartItemsContainer.innerHTML = '<p class="error-message">Failed to load cart items.</p>';
            cartSummaryDiv.style.display = 'none';
        }
    }

    function renderCart(cart) {
        cartItemsContainer.innerHTML = '';
        if (cart.items.length === 0) {
            cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
            cartSummaryDiv.style.display = 'none';
            return;
        }

        let total = 0;
        cart.items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'cart-item';
            const itemSubtotal = item.product.price * item.quantity;
            total += itemSubtotal;

            itemDiv.innerHTML = `
                <img src="${item.product.image_url || '/static/images/default_book.png'}" alt="${item.product.name}">
                <div class="item-details">
                    <h3>${item.product.name}</h3>
                    <p>Price: $${item.product.price.toFixed(2)}</p>
                    <div class="quantity-controls">
                        <label for="quantity-${item.product.id}">Quantity:</label>
                        <input type="number" id="quantity-${item.product.id}" value="${item.quantity}" min="1" data-product-id="${item.product.id}" class="quantity-input">
                        <button class="remove-item-button button secondary" data-product-id="${item.product.id}">Remove</button>
                    </div>
                    <p class="item-subtotal">Subtotal: $${itemSubtotal.toFixed(2)}</p>
                </div>
            `;
            cartItemsContainer.appendChild(itemDiv);
        });

        cartTotalSpan.textContent = `$${total.toFixed(2)}`;
        cartSummaryDiv.style.display = 'block';

        // Add event listeners for quantity changes and remove buttons
        cartItemsContainer.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', updateCartItemQuantity);
        });
        cartItemsContainer.querySelectorAll('.remove-item-button').forEach(button => {
            button.addEventListener('click', removeCartItem);
        });
    }

    async function updateCartItemQuantity(event) {
        const productId = event.target.dataset.productId;
        const newQuantity = parseInt(event.target.value);

        if (isNaN(newQuantity) || newQuantity < 1) {
            displayMessage(errorMessage, 'Quantity must be at least 1.', true);
            event.target.value = event.target.defaultValue; // Revert to previous valid value
            return;
        }

        try {
            const response = await fetch(`/api/cart/items/${productId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ quantity: newQuantity })
            });

            const data = await response.json();

            if (response.ok) {
                fetchCart(); // Re-render cart to update totals
            } else {
                displayMessage(errorMessage, data.detail || 'Failed to update quantity.', true);
                event.target.value = event.target.defaultValue; // Revert on error
            }
        } catch (error) {
            console.error('Error updating cart item quantity:', error);
            displayMessage(errorMessage, 'An unexpected error occurred.', true);
            event.target.value = event.target.defaultValue; // Revert on error
        }
    }

    async function removeCartItem(event) {
        const productId = event.target.dataset.productId;

        try {
            const response = await fetch(`/api/cart/items/${productId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                fetchCart(); // Re-render cart
            } else {
                displayMessage(errorMessage, data.detail || 'Failed to remove item.', true);
            }
        } catch (error) {
            console.error('Error removing cart item:', error);
            displayMessage(errorMessage, 'An unexpected error occurred.', true);
        }
    }

    checkoutButton.addEventListener('click', () => {
        window.location.href = '/checkout';
    });

    fetchCart();
    updateAuthUI();
    updateCartCount();
});
