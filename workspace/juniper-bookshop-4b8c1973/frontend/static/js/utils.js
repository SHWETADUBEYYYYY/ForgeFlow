// utils.js

// Function to make API requests
async function apiRequest(method, url, data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    
    // Handle 204 No Content explicitly
    if (response.status === 204) {
        return {}; // Return an empty object for no content
    }

    const responseData = await response.json();

    if (!response.ok) {
        throw new Error(responseData.detail || 'Something went wrong');
    }

    return responseData;
}

// Function to display error messages
function displayErrorMessage(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

// Function to hide error messages
function hideErrorMessage(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
}

// Function to update auth links based on login status
function updateAuthLinks() {
    const username = localStorage.getItem('username');
    const authLinks = document.getElementById('auth-links');
    const userInfo = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');
    const logoutButton = document.getElementById('logout-button');

    if (username) {
        if (authLinks) authLinks.style.display = 'none';
        if (userInfo) userInfo.style.display = 'inline';
        if (usernameDisplay) usernameDisplay.textContent = username;
        if (logoutButton) logoutButton.addEventListener('click', handleLogout);
    } else {
        if (authLinks) authLinks.style.display = 'inline';
        if (userInfo) userInfo.style.display = 'none';
    }
}

// Function to handle logout
async function handleLogout() {
    try {
        await apiRequest('POST', '/api/auth/logout');
        localStorage.removeItem('username');
        updateAuthLinks();
        updateCartCount(); // Update cart count after logout
        window.location.href = '/login'; // Redirect to login page
    } catch (error) {
        console.error('Logout failed:', error.message);
        alert('Logout failed: ' + error.message);
    }
}

// Function to update cart count in the header
async function updateCartCount() {
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        try {
            const data = await apiRequest('GET', '/api/cart/count');
            cartCountElement.textContent = data.count;
        } catch (error) {
            console.error('Failed to fetch cart count:', error.message);
            cartCountElement.textContent = '0'; // Default to 0 on error
        }
    }
}

// Initialize auth links and cart count on page load
document.addEventListener('DOMContentLoaded', () => {
    updateAuthLinks();
    updateCartCount();
});
