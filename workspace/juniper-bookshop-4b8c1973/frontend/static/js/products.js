document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const productId = urlParams.get('id');

    const productDetailSection = document.getElementById('product-detail');
    const productTitle = document.getElementById('product-title');
    const productAuthor = document.getElementById('product-author');
    const productPrice = document.getElementById('product-price');
    const productDescription = document.getElementById('product-description');
    const productImage = document.getElementById('product-image');
    const quantityInput = document.getElementById('quantity-input');
    const addToCartButton = document.getElementById('add-to-cart-button');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');

    if (window.location.pathname === '/') {
        // Product listing page
        const productsContainer = document.getElementById('products-container');
        if (!productsContainer) return;

        try {
            const response = await fetch('/api/products');
            const products = await response.json();

            if (products.length === 0) {
                productsContainer.innerHTML = '<p>No products available.</p>';
                return;
            }

            products.forEach(product => {
                const productCard = document.createElement('div');
                productCard.className = 'product-card';
                productCard.innerHTML = `
                    <img src="${product.image_url || '/static/images/default_book.png'}" alt="${product.name}">
                    <h3>${product.name}</h3>
                    <p class="author">${product.author}</p>
                    <p class="price">$${product.price.toFixed(2)}</p>
                    <a href="/product?id=${product.id}" class="button">View Details</a>
                `;
                productsContainer.appendChild(productCard);
            });
        } catch (error) {
            console.error('Error fetching products:', error);
            productsContainer.innerHTML = '<p class="error-message">Failed to load products. Please try again later.</p>';
        }
    } else if (window.location.pathname === '/product' && productId) {
        // Product detail page
        if (!productDetailSection) return;

        try {
            const response = await fetch(`/api/products/${productId}`);
            if (!response.ok) {
                if (response.status === 404) {
                    productDetailSection.innerHTML = '<p class="error-message">Product not found.</p>';
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return;
            }
            const product = await response.json();

            productTitle.textContent = product.name;
            productAuthor.textContent = `by ${product.author}`;
            productPrice.textContent = `$${product.price.toFixed(2)}`;
            productDescription.textContent = product.description;
            productImage.src = product.image_url || '/static/images/default_book.png';
            productImage.alt = product.name;

            addToCartButton.addEventListener('click', async () => {
                const quantity = parseInt(quantityInput.value);
                if (isNaN(quantity) || quantity < 1) {
                    displayMessage(errorMessage, 'Please enter a valid quantity.', true);
                    return;
                }

                try {
                    const response = await fetch('/api/cart/items', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ product_id: product.id, quantity: quantity })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        displayMessage(successMessage, `${quantity} x ${product.name} added to cart!`, false);
                        updateCartCount();
                    } else {
                        displayMessage(errorMessage, data.detail || 'Failed to add item to cart.', true);
                    }
                } catch (error) {
                    console.error('Error adding to cart:', error);
                    displayMessage(errorMessage, 'An unexpected error occurred.', true);
                }
            });

        } catch (error) {
            console.error('Error fetching product details:', error);
            productDetailSection.innerHTML = '<p class="error-message">Failed to load product details. Please try again later.</p>';
        }
    }

    updateAuthUI();
    updateCartCount();
});
