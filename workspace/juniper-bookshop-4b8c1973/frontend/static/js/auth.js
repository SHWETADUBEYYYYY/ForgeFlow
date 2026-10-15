// auth.js

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            hideErrorMessage('error-message');

            const username = loginForm.username.value;
            const password = loginForm.password.value;

            try {
                const data = await apiRequest('POST', '/api/auth/login', { username, password });
                localStorage.setItem('username', data.username);
                updateAuthLinks();
                updateCartCount();
                window.location.href = '/'; // Redirect to home page
            } catch (error) {
                displayErrorMessage('error-message', error.message);
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            hideErrorMessage('error-message');

            const username = registerForm.username.value;
            const password = registerForm.password.value;

            try {
                await apiRequest('POST', '/api/auth/register', { username, password });
                alert('Registration successful! Please log in.');
                window.location.href = '/login'; // Redirect to login page
            } catch (error) {
                displayErrorMessage('error-message', error.message);
            }
        });
    }
});
