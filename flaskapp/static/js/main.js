// Session and Authentication Management
const SessionManager = {
    token: null,
    lastCheck: 0,
    checkInterval: 5 * 60 * 1000, // 5 minutes
    retryAttempts: 0,
    maxRetries: 3,
    offlineMode: false,
    pendingRefresh: null,

    async refreshSession(user, force = false) {
        if (!user) {
            console.log('No user to refresh session for');
            return false;
        }

        try {
            if (!this.shouldRefresh() && !force) {
                const isValid = await this.validateSession();
                if (isValid) {
                    console.log('Session is valid, no refresh needed');
                    return true;
                }
                console.log('Session validation failed, refreshing token');
            }

            console.log('Refreshing session token');
            const token = await user.getIdToken(true);
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Authorization': token,
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Session refresh failed');
            }

            const data = await response.json();
            if (!data.user) {
                throw new Error('Invalid user data from server');
            }

            this.token = token;
            this.lastCheck = Date.now();
            this.retryAttempts = 0;
            this.updateLastActivity();
            return true;

        } catch (error) {
            if (error.name === 'TypeError' && !navigator.onLine) {
                console.log('Offline mode activated during refresh');
                this.offlineMode = true;
                this.pendingRefresh = () => this.refreshSession(user, true);
                return true;
            }

            console.error('Session refresh failed:', error);
            
            if (this.retryAttempts < this.maxRetries) {
                this.retryAttempts++;
                const backoff = Math.min(1000 * Math.pow(2, this.retryAttempts), 10000);
                console.log(`Retrying session refresh in ${backoff}ms (attempt ${this.retryAttempts})`);
                setTimeout(() => this.refreshSession(user, true), backoff);
            } else {
                this.clearSession();
            }
            return false;
        }
    },

    shouldRefresh() {
        const now = Date.now();
        return !this.lastCheck || (now - this.lastCheck) > this.checkInterval;
    },

    async validateSession() {
        if (!this.token) return false;
        try {
            const response = await fetch('/auth/validate', {
                method: 'POST',
                headers: {
                    'Authorization': this.token,
                    'Content-Type': 'application/json'
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Session validation failed:', error);
            return false;
        }
    },

    updateLastActivity() {
        this.lastActivity = Date.now();
        localStorage.setItem('lastActivity', this.lastActivity);
    },

    clearSession() {
        this.token = null;
        this.lastCheck = 0;
        this.retryAttempts = 0;
        localStorage.removeItem('lastActivity');
    }
};

// Initialize Firebase and set up event handlers
document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('login');
    const logoutForm = document.getElementById('logout-form');
    
    loginBtn?.addEventListener('click', async () => {
        try {
            const provider = new firebase.auth.GoogleAuthProvider();
            await auth.signInWithPopup(provider);
        } catch (error) {
            console.error('Login error:', error);
            showMessage('Login failed: ' + error.message, 'error');
        }
    });

    let authChangeInProgress = false;
    auth.onAuthStateChanged(async (user) => {
        if (authChangeInProgress) return;
        authChangeInProgress = true;
        
        try {
            console.log('Auth state changed:', user ? user.email : 'logged out');
            
            if (user) {
                const success = await SessionManager.refreshSession(user, true);
                if (success) {
                    showMessage('Successfully logged in!', 'success');
                    updateUI(true);
                } else {
                    console.error('Failed to establish session');
                    await auth.signOut();
                    showMessage('Failed to establish session', 'error');
                    updateUI(false);
                }
            } else {
                SessionManager.clearSession();
                updateUI(false);
            }
        } catch (error) {
            console.error('Auth state change error:', error);
            showMessage('Authentication error: ' + error.message, 'error');
            updateUI(false);
        } finally {
            authChangeInProgress = false;
        }
    });

    async function handleLogout(e) {
        e.preventDefault();
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': SessionManager.token,
                    'Content-Type': 'application/json'
                }
            });
            await auth.signOut();
            showMessage('Successfully logged out!', 'success');
        } catch (error) {
            console.error('Logout error:', error);
            showMessage('Logout failed: ' + error.message, 'error');
        }
    }

    logoutForm?.addEventListener('submit', handleLogout);
});

function showMessage(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    alertContainer.querySelectorAll(`.alert-${type}`).forEach(alert => {
        if (alert.textContent.trim() === message.trim()) {
            alert.remove();
        }
    });

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} mb-4 px-4 py-3 rounded relative`;
    
    switch(type) {
        case 'success':
            alert.className += ' bg-green-100 border-green-400 text-green-700';
            break;
        case 'error':
            alert.className += ' bg-red-100 border-red-400 text-red-700';
            break;
        default:
            alert.className += ' bg-blue-100 border-blue-400 text-blue-700';
    }
    
    alert.innerHTML = `
        <span class="block sm:inline">${message}</span>
        <button class="absolute top-0 right-0 px-4 py-3" onclick="this.parentElement.remove()">
            <svg class="h-4 w-4 fill-current" role="button" viewBox="0 0 20 20">
                <path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/>
            </svg>
        </button>
    `;
    
    alertContainer.appendChild(alert);
    setTimeout(() => {
        if (alert.parentNode === alertContainer) {
            alert.remove();
        }
    }, 5000);
}

function updateUI(isAuthenticated) {
    const loggedInElements = document.querySelectorAll('.logged-in');
    const loggedOutElements = document.querySelectorAll('.logged-out');

    loggedInElements.forEach(el => {
        el.style.removeProperty('display');
        el.style.display = isAuthenticated ? 'block' : 'none';
    });
    
    loggedOutElements.forEach(el => {
        el.style.removeProperty('display');
        el.style.display = isAuthenticated ? 'none' : 'block';
    });
}
