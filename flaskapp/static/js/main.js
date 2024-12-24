// Session and Authentication Management
const SessionManager = {
    token: null,
    lastCheck: 0,
    checkInterval: 5 * 60 * 1000,
    retryAttempts: 0,
    maxRetries: 3,
    offlineMode: false,
    pendingRefresh: null,
    sessionTimeout: 60 * 60 * 1000, // 60 minutes
    activityTimeout: null,
    heartbeatInterval: null,
    lastActivity: Date.now(),
    _clearingSession: false,

    async init() {
        try {
            const stored = localStorage.getItem('sessionState');
            if (stored) {
                const { token, lastCheck, lastActivity } = JSON.parse(stored);
                if (Date.now() - lastActivity < this.sessionTimeout) {
                    this.token = token;
                    this.lastCheck = lastCheck;
                    this.lastActivity = lastActivity;
                } else {
                    await this.clearSession();
                    return;
                }
            }
        } catch (e) {
            await this.clearSession();
            return;
        }

        this.setupStorageListener();
        this.setupOfflineHandler();
        this.setupActivityTracking();
        this.startHeartbeat();
    },

    setupStorageListener() {
        window.addEventListener('storage', async (e) => {
            if (e.key === 'sessionState') {
                try {
                    if (e.newValue) {
                        const { token, lastCheck, lastActivity } = JSON.parse(e.newValue);
                        if (Date.now() - lastActivity < this.sessionTimeout) {
                            this.token = token;
                            this.lastCheck = lastCheck;
                            this.lastActivity = lastActivity;
                        } else {
                            await this.clearSession();
                        }
                    } else {
                        await this.clearSession();
                    }
                } catch (e) {
                    await this.clearSession();
                }
            }
        });
    },

    setupOfflineHandler() {
        window.addEventListener('online', async () => {
            this.offlineMode = false;
            if (this.pendingRefresh) {
                await this.pendingRefresh();
                this.pendingRefresh = null;
            }
        });

        window.addEventListener('offline', () => {
            this.offlineMode = true;
        });
    },

    setupActivityTracking() {
        const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];
        const updateActivity = this.debounce(() => this.updateLastActivity(), 1000);
        
        events.forEach(event => {
            window.addEventListener(event, updateActivity, { passive: true });
        });
    },

    startHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        this.heartbeatInterval = setInterval(async () => {
            if (!this.token || this.offlineMode) return;
            
            try {
                const response = await fetch('/auth/heartbeat', {
                    method: 'POST',
                    headers: {
                        'Authorization': this.token,
                        'Content-Type': 'application/json'
                    },
                    credentials: 'same-origin'
                });
                
                if (!response.ok) {
                    throw new Error('Heartbeat failed');
                }
            } catch (e) {
                console.error('Heartbeat error:', e);
            }
        }, 60000);
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    async updateLastActivity() {
        this.lastActivity = Date.now();
        if (this.activityTimeout) {
            clearTimeout(this.activityTimeout);
        }
        
        this.activityTimeout = setTimeout(async () => {
            if (Date.now() - this.lastActivity >= this.sessionTimeout) {
                await this.clearSession();
                window.location.reload();
            }
        }, this.sessionTimeout);

        this.saveState();
    },

    saveState() {
        try {
            localStorage.setItem('sessionState', JSON.stringify({
                token: this.token,
                lastCheck: this.lastCheck,
                lastActivity: this.lastActivity
            }));
        } catch (e) {
            console.error('Failed to save session state:', e);
        }
    },

    async clearSession() {
        if (this._clearingSession) return;
        this._clearingSession = true;

        try {
            this.token = null;
            this.lastCheck = 0;
            this.retryAttempts = 0;
            this.pendingRefresh = null;
            this.lastActivity = 0;
            
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.heartbeatInterval = null;
            }
            if (this.activityTimeout) {
                clearTimeout(this.activityTimeout);
                this.activityTimeout = null;
            }

            localStorage.removeItem('sessionState');

            if (this.token) {
                try {
                    await fetch('/auth/logout', {
                        method: 'POST',
                        headers: {
                            'Authorization': this.token,
                            'Content-Type': 'application/json'
                        },
                        credentials: 'same-origin'
                    });
                } catch (e) {
                    console.warn('Logout request failed:', e);
                }
            }
        } catch (e) {
            console.error('Failed to clear session:', e);
        } finally {
            this._clearingSession = false;
        }
    },

    shouldRefresh() {
        if (this.offlineMode) return false;
        
        return !this.token || 
               (Date.now() - this.lastCheck >= this.checkInterval) || 
               (Date.now() - this.lastActivity >= this.sessionTimeout) ||
               this.retryAttempts > 0;
    },

    async validateSession() {
        if (!this.token) return false;

        try {
            console.log('Validating session token');
            const response = await fetch('/auth/validate', {
                method: 'POST',
                headers: {
                    'Authorization': this.token,
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                console.warn('Session validation failed:', response.status);
                if (response.status === 401) {
                    await this.clearSession();
                }
                return false;
            }

            const data = await response.json();
            if (!data.valid) {
                console.warn('Session invalid:', data.message);
                await this.clearSession();
                return false;
            }

            this.updateLastActivity();
            return true;
        } catch (e) {
            console.error('Session validation error:', e);
            return navigator.onLine ? false : true;
        }
    },

    async refreshSession(user, force = false) {
        if (force) {
            await this.clearSession();
        }

        if (this.offlineMode) {
            this.pendingRefresh = () => this.refreshSession(user, true);
            return true;
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
                throw new Error('Session refresh failed');
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
                await new Promise(resolve => setTimeout(resolve, backoff));
                return this.refreshSession(user, true);
            }

            console.error('Max retry attempts reached, clearing session');
            await this.clearSession();
            return false;
        }
    }
};

// Initialize Firebase and set up event handlers
document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('login');
    const logoutForm = document.getElementById('logout-form');
    const loggedInElements = document.querySelectorAll('.logged-in');
    const loggedOutElements = document.querySelectorAll('.logged-out');

    const auth = firebase.auth();
    const provider = new firebase.auth.GoogleAuthProvider();
    provider.setCustomParameters({
        prompt: 'select_account'
    });
    
    SessionManager.init();

    function updateUI(isAuthenticated, isOffline = false) {
        console.log('Updating UI:', { isAuthenticated, isOffline });
        
        loggedInElements.forEach(el => {
            el.style.removeProperty('display');
            el.style.display = isAuthenticated ? 'block' : 'none';
            if (isOffline) {
                el.classList.add('offline-mode');
            } else {
                el.classList.remove('offline-mode');
            }
        });
        
        loggedOutElements.forEach(el => {
            el.style.removeProperty('display');
            el.style.display = isAuthenticated ? 'none' : 'block';
        });
    }

    let authChangeInProgress = false;
    auth.onAuthStateChanged(async (user) => {
        console.log('Auth state changed:', { user: user?.email, authChangeInProgress });
        
        if (authChangeInProgress) return;
        try {
            authChangeInProgress = true;
            if (user) {
                const success = await SessionManager.refreshSession(user);
                if (!success) {
                    throw new Error('Authentication failed after retries');
                }
                updateUI(true, SessionManager.offlineMode);
            } else {
                console.log('User logged out, clearing session');
                await SessionManager.clearSession();
                updateUI(false);
            }
        } catch (error) {
            console.error('Auth state error:', error);
            showMessage(error.message, 'error');
            await SessionManager.clearSession();
            updateUI(false);
            
            if (auth.currentUser) {
                try {
                    await auth.signOut();
                } catch (signOutError) {
                    console.error('Sign out error:', signOutError);
                }
            }
        } finally {
            authChangeInProgress = false;
        }
    });

    if (loginBtn) {
        let loginInProgress = false;
        loginBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (loginInProgress) {
                console.log('Login already in progress');
                return;
            }
            
            try {
                loginInProgress = true;
                loginBtn.disabled = true;
                await auth.signInWithPopup(provider);
            } catch (error) {
                console.error('Login error:', error);
                showMessage('Login failed: ' + error.message, 'error');
            } finally {
                loginBtn.disabled = false;
                loginInProgress = false;
            }
        });
    }

    if (logoutForm) {
        console.log('Setting up logout form handler');
        let logoutInProgress = false;
        
        const handleLogout = async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Logout initiated');
            
            if (logoutInProgress) {
                console.log('Logout already in progress');
                return;
            }
            
            try {
                logoutInProgress = true;
                console.log('Starting logout process');
                
                updateUI(false);
                
                await Promise.all([
                    SessionManager.clearSession(),
                    auth.signOut()
                ]);
                
                console.log('Logout complete');
                showMessage('Successfully logged out', 'success');
            } catch (error) {
                console.error('Logout error:', error);
                showMessage('Logout failed: ' + error.message, 'error');
                updateUI(true, SessionManager.offlineMode);
            } finally {
                logoutInProgress = false;
            }
        };
        
        logoutForm.removeEventListener('submit', handleLogout);
        logoutForm.addEventListener('submit', handleLogout);
        
        const logoutBtn = logoutForm.querySelector('#logout');
        if (logoutBtn) {
            logoutBtn.removeEventListener('click', handleLogout);
            logoutBtn.addEventListener('click', handleLogout);
        }
    } else {
        console.warn('Logout form not found in the document');
    }

    let visibilityTimeout;
    document.addEventListener('visibilitychange', () => {
        if (visibilityTimeout) {
            clearTimeout(visibilityTimeout);
        }
        if (!document.hidden && auth.currentUser) {
            visibilityTimeout = setTimeout(async () => {
                try {
                    await SessionManager.refreshSession(auth.currentUser, true);
                    updateUI(true, SessionManager.offlineMode);
                } catch (error) {
                    console.error('Visibility change session refresh failed:', error);
                }
            }, 1000);
        }
    });

    setInterval(async () => {
        if (auth.currentUser && !SessionManager.offlineMode) {
            try {
                const isValid = await SessionManager.validateSession();
                if (!isValid) {
                    await SessionManager.refreshSession(auth.currentUser, true);
                }
                updateUI(true, SessionManager.offlineMode);
            } catch (error) {
                console.error('Periodic session validation failed:', error);
            }
        }
    }, SessionManager.checkInterval);
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
