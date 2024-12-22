// Firebase Authentication handling
document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('login');
    const logoutForm = document.getElementById('logout-form');
    const loggedInElements = document.querySelectorAll('.logged-in');
    const loggedOutElements = document.querySelectorAll('.logged-out');

    // Initialize Firebase Auth
    const auth = firebase.auth();
    const provider = new firebase.auth.GoogleAuthProvider();

    // Monitor auth state
    auth.onAuthStateChanged(async function(user) {
        try {
            if (user) {
                // User is signed in
                console.log('User is signed in:', user.email);
                
                // Force token refresh to ensure we have a valid token
                const token = await user.getIdToken(true);
                
                try {
                    // Authenticate with backend
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        // Show logged in state
                        loggedInElements.forEach(el => el.style.display = 'block');
                        loggedOutElements.forEach(el => el.style.display = 'none');
                        showMessage('Successfully logged in!', 'success');
                        console.log('Backend authentication successful:', data);
                    } else {
                        // Handle backend auth failure
                        const data = await response.json();
                        throw new Error(data.message || 'Backend authentication failed');
                    }
                } catch (error) {
                    console.error('Backend auth error:', error);
                    showMessage(error.message, 'error');
                    // Clear session storage
                    sessionStorage.clear();
                    // Sign out from Firebase
                    await auth.signOut();
                }
            } else {
                // User is signed out
                console.log('User is signed out');
                loggedInElements.forEach(el => el.style.display = 'none');
                loggedOutElements.forEach(el => el.style.display = 'block');
                // Clear any existing session data
                sessionStorage.clear();
            }
        } catch (error) {
            console.error('Auth state change error:', error);
            showMessage('Authentication error. Please try again.', 'error');
            // Clear session storage and sign out on error
            sessionStorage.clear();
            await auth.signOut();
        }
    });

    if (loginBtn) {
        loginBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            try {
                await auth.signInWithPopup(provider);
            } catch (error) {
                console.error('Login error:', error);
                showMessage('Failed to log in: ' + error.message, 'error');
            }
        });
    }

    if (logoutForm) {
        logoutForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            try {
                // First, sign out from Firebase
                await auth.signOut();
                
                // Then, sign out from backend
                const response = await fetch('/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    showMessage('Successfully logged out!', 'success');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                } else {
                    throw new Error('Backend logout failed');
                }
            } catch (error) {
                console.error('Logout error:', error);
                showMessage('Failed to log out: ' + error.message, 'error');
            }
        });
    }

    // Utility function to show messages to the user
    function showMessage(message, type = 'info') {
        const flashContainer = document.createElement('div');
        flashContainer.className = `rounded-md bg-${type}-50 p-4 mb-4`;
        
        const content = `
            <div class="flex">
                <div class="flex-shrink-0">
                    ${type === 'success' ? `
                        <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                    ` : `
                        <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                        </svg>
                    `}
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-${type}-800">${message}</p>
                </div>
            </div>
        `;
        
        flashContainer.innerHTML = content;
        
        // Insert at the top of the main content
        const main = document.querySelector('main');
        main.insertBefore(flashContainer, main.firstChild);
        
        // Remove after 5 seconds
        setTimeout(() => {
            flashContainer.remove();
        }, 5000);
    }
});
