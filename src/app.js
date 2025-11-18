// IPFS Solana Manager - Frontend Application
// Secure, modern interface for IPFS and Solana operations

const API_BASE = 'http://127.0.0.1:8765';

// Debug: Check Tauri environment
setTimeout(() => {
    console.log('=== Tauri Environment Check (after load) ===');
    console.log('window.__TAURI_INTERNALS__:', !!window.__TAURI_INTERNALS__);
    console.log('window.__TAURI_INVOKE__:', !!window.__TAURI_INVOKE__);
    console.log('window.__TAURI__:', !!window.__TAURI__);
    if (window.__TAURI__) {
        console.log('window.__TAURI__.dialog:', !!window.__TAURI__.dialog);
        console.log('window.__TAURI__.shell:', !!window.__TAURI__.shell);
    }
    console.log('Location:', window.location.href);
    console.log('===========================================');
}, 500);

// State management
const state = {
    selectedFilePath: null,
    lastCID: null,
    isWalletVerified: false,
    authToken: null,
    username: null
};

// DOM Elements - Login
const loginElements = {
    loginScreen: document.getElementById('login-screen'),
    mainApp: document.getElementById('main-app'),
    loginForm: document.getElementById('login-form'),
    usernameInput: document.getElementById('login-username'),
    passwordInput: document.getElementById('login-password'),
    loginResult: document.getElementById('login-result'),
    userInfo: document.getElementById('user-info'),
    logoutBtn: document.getElementById('logout-btn'),
    loginLogo: document.getElementById('login-logo'),
    secretResetBtn: document.getElementById('secret-reset-btn')
};

// DOM Elements - Main App
const elements = {
    selectFileBtn: document.getElementById('select-file-btn'),
    selectedFileName: document.getElementById('selected-file-name'),
    uploadBtn: document.getElementById('upload-btn'),
    uploadResult: document.getElementById('upload-result'),
    
    privateKeyInput: document.getElementById('private-key'),
    toggleKeyBtn: document.getElementById('toggle-key-visibility'),
    verifyWalletBtn: document.getElementById('verify-wallet-btn'),
    registerBtn: document.getElementById('register-btn'),
    walletResult: document.getElementById('wallet-result'),
    
    cidInput: document.getElementById('cid-input'),
    pasteCidBtn: document.getElementById('paste-cid-btn'),
    openBrowserBtn: document.getElementById('open-browser-btn'),
    downloadBtn: document.getElementById('download-btn'),
    accessResult: document.getElementById('access-result'),
    
    ipfsStatus: document.getElementById('ipfs-status'),
    solanaStatus: document.getElementById('solana-status')
};

// Initialize app
async function init() {
    setupLoginListeners();
    await checkFirstTimeSetup();
    checkExistingSession();
}

// Setup login event listeners
function setupLoginListeners() {
    loginElements.loginForm.addEventListener('submit', handleLogin);
    loginElements.logoutBtn?.addEventListener('click', handleLogout);
    
    // Secret easter egg: Click logo 5 times to reveal reset button
    let clickCount = 0;
    let clickTimer = null;
    
    loginElements.loginLogo?.addEventListener('click', () => {
        clickCount++;
        
        // Reset counter after 2 seconds of no clicks
        clearTimeout(clickTimer);
        clickTimer = setTimeout(() => {
            clickCount = 0;
        }, 2000);
        
        // Show reset button after 5 clicks
        if (clickCount === 5) {
            loginElements.secretResetBtn.style.display = 'block';
            loginElements.loginLogo.style.color = '#D13438';
            clickCount = 0;
        }
    });
    
    // Handle secret reset button
    loginElements.secretResetBtn?.addEventListener('click', resetApplication);
}

// Check for first-time setup and show credentials
async function checkFirstTimeSetup() {
    try {
        const response = await fetch(`${API_BASE}/auth/first-time-check`);
        const data = await response.json();
        
        if (data.is_first_time && data.username && data.password) {
            showFirstTimeCredentials(data.username, data.password);
        }
    } catch (error) {
        console.error('First-time check failed:', error);
    }
}

// Show first-time credentials in a modal
function showFirstTimeCredentials(username, password) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    modal.innerHTML = `
        <div style="
            background: #FAFAFA;
            border: 2px solid #EDEBE9;
            padding: 40px;
            max-width: 600px;
            width: 90%;
        ">
            <div style="
                padding-bottom: 20px;
                border-bottom: 2px solid #0078D4;
                margin-bottom: 24px;
            ">
                <h1 style="
                    margin: 0;
                    font-size: 20px;
                    font-weight: 600;
                    color: #323130;
                ">Account Credentials</h1>
            </div>
            
            <div style="margin-bottom: 20px;">
                <p style="
                    margin: 0;
                    color: #605E5C;
                    font-size: 14px;
                    line-height: 1.5;
                ">
                    Your secure login credentials have been generated. Save them immediately in a secure location.
                </p>
            </div>
            
            <div style="
                background: #FFFFFF;
                border: 1px solid #EDEBE9;
                padding: 20px;
                margin: 20px 0;
            ">
                <div style="margin-bottom: 16px;">
                    <label style="
                        display: block;
                        font-size: 13px;
                        font-weight: 600;
                        margin-bottom: 6px;
                        color: #323130;
                    ">USERNAME</label>
                    <div style="
                        font-family: 'Courier New', monospace;
                        font-size: 14px;
                        padding: 8px 12px;
                        background: #FFFFFF;
                        border: 1px solid #EDEBE9;
                        cursor: pointer;
                        color: #323130;
                    " 
                    onclick="navigator.clipboard.writeText('${username}'); this.style.borderColor='#0078D4'; this.style.borderWidth='2px'; this.style.padding='7px 11px'; setTimeout(() => { this.style.borderColor='#EDEBE9'; this.style.borderWidth='1px'; this.style.padding='8px 12px'; }, 1000);"
                    onmouseover="this.style.background='#F3F2F1'"
                    onmouseout="this.style.background='#FFFFFF'">
                        ${username}
                    </div>
                </div>
                
                <div>
                    <label style="
                        display: block;
                        font-size: 13px;
                        font-weight: 600;
                        margin-bottom: 6px;
                        color: #323130;
                    ">PASSWORD</label>
                    <div style="
                        font-family: 'Courier New', monospace;
                        font-size: 14px;
                        padding: 8px 12px;
                        background: #FFFFFF;
                        border: 1px solid #EDEBE9;
                        cursor: pointer;
                        word-break: break-all;
                        color: #323130;
                    " 
                    onclick="navigator.clipboard.writeText('${password}'); this.style.borderColor='#0078D4'; this.style.borderWidth='2px'; this.style.padding='7px 11px'; setTimeout(() => { this.style.borderColor='#EDEBE9'; this.style.borderWidth='1px'; this.style.padding='8px 12px'; }, 1000);"
                    onmouseover="this.style.background='#F3F2F1'"
                    onmouseout="this.style.background='#FFFFFF'">
                        ${password}
                    </div>
                </div>
            </div>
            
            <div style="
                background: #F3F2F1;
                border-left: 3px solid #323130;
                padding: 16px;
                margin: 20px 0;
            ">
                <div style="
                    font-weight: 600;
                    margin-bottom: 8px;
                    font-size: 13px;
                    color: #323130;
                ">Important Security Notice</div>
                <ul style="
                    margin: 0;
                    padding-left: 20px;
                    font-size: 13px;
                    line-height: 1.6;
                    color: #605E5C;
                ">
                    <li>These credentials will never be shown again</li>
                    <li>Click any field above to copy to clipboard</li>
                    <li>Store in a secure password manager</li>
                    <li>Loss of credentials requires application reset</li>
                </ul>
            </div>
            
            <button id="credentials-saved-btn" style="
                background: #0078D4;
                color: white;
                border: none;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                font-family: 'Inter', sans-serif;
            " 
            onmouseover="this.style.background='#005A9E'" 
            onmouseout="this.style.background='#0078D4'">
                I Have Saved These Credentials
            </button>
            
            <p style="
                margin: 16px 0 0 0;
                font-size: 12px;
                color: #605E5C;
                text-align: center;
            ">
                No backup file is created. Save these credentials now or they are lost forever.
            </p>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto-fill the login form
    loginElements.usernameInput.value = username;
    loginElements.passwordInput.value = password;
    
    // Handle button click
    document.getElementById('credentials-saved-btn').addEventListener('click', () => {
        modal.remove();
    });
}

// Check for existing session
function checkExistingSession() {
    const token = localStorage.getItem('authToken');
    const username = localStorage.getItem('username');
    
    if (token && username) {
        state.authToken = token;
        state.username = username;
        showMainApp();
    }
}

// Handle login
async function handleLogin(e) {
    e.preventDefault();
    
    const username = loginElements.usernameInput.value.trim();
    const password = loginElements.passwordInput.value;
    
    if (!username || !password) {
        showLoginError('Please enter username and password');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.authToken = data.token;
            state.username = data.username;
            
            // Save to localStorage
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('username', data.username);
            
            showMainApp();
        } else {
            showLoginError(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        showLoginError('Connection error. Please check if the server is running.');
    }
}

// Handle logout
async function handleLogout() {
    try {
        if (state.authToken) {
            await fetch(`${API_BASE}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${state.authToken}`
                }
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Clear state
    state.authToken = null;
    state.username = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    
    showLoginScreen();
}

// Show login error
function showLoginError(message) {
    loginElements.loginResult.textContent = message;
    loginElements.loginResult.className = 'login-result error';
}

// Show main app
function showMainApp() {
    loginElements.loginScreen.style.display = 'none';
    loginElements.mainApp.style.display = 'block';
    loginElements.userInfo.textContent = `Logged in as: ${state.username}`;
    
    setupEventListeners();
    checkHealth();
}

// Show login screen
function showLoginScreen() {
    loginElements.loginScreen.style.display = 'flex';
    loginElements.mainApp.style.display = 'none';
    loginElements.usernameInput.value = '';
    loginElements.passwordInput.value = '';
    loginElements.loginResult.className = 'login-result';
}

// Reset application (nuclear option)
async function resetApplication() {
    const confirmed = confirm(
        'DANGER: This will permanently delete all user data and generate new credentials.\n\n' +
        'This action cannot be undone.\n\n' +
        'Are you absolutely sure?'
    );
    
    if (!confirmed) return;
    
    const doubleConfirmed = confirm(
        'FINAL WARNING: All data will be lost.\n\n' +
        'Type OK in the next prompt to proceed.'
    );
    
    if (!doubleConfirmed) return;
    
    const finalCheck = prompt('Type RESET in capital letters to confirm:');
    
    if (finalCheck !== 'RESET') {
        alert('Reset cancelled.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/reset-application`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Application reset successful!\n\nNew credentials will be shown in a moment.\n\nPlease reload the page.');
            // Force reload to show new credentials
            window.location.reload();
        } else {
            alert('Reset failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Reset error:', error);
        alert('Reset failed: ' + error.message);
    }
}

// Make reset function available globally
window.resetApplication = resetApplication;

// Reset application (nuclear option)
async function resetApplication() {
    const confirmed = confirm(
        'DANGER: This will permanently delete all user data and generate new credentials.\n\n' +
        'This action cannot be undone.\n\n' +
        'Are you absolutely sure?'
    );
    
    if (!confirmed) return;
    
    const doubleConfirmed = confirm(
        'FINAL WARNING: All data will be lost.\n\n' +
        'Click OK to proceed with reset.'
    );
    
    if (!doubleConfirmed) return;
    
    const finalCheck = prompt('Type RESET in capital letters to confirm:');
    
    if (finalCheck !== 'RESET') {
        alert('Reset cancelled.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/reset-application`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Application reset successful!\n\nNew credentials will be shown in a moment.\n\nPlease reload the page.');
            // Force reload to show new credentials
            window.location.reload();
        } else {
            alert('Reset failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Reset error:', error);
        alert('Reset failed: ' + error.message);
    }
}

// Setup main app event listeners
function setupEventListeners() {
    elements.selectFileBtn.addEventListener('click', selectFile);
    elements.uploadBtn.addEventListener('click', uploadFile);
    
    elements.toggleKeyBtn.addEventListener('click', toggleKeyVisibility);
    elements.verifyWalletBtn.addEventListener('click', verifyWallet);
    elements.registerBtn.addEventListener('click', registerOnSolana);
    
    elements.pasteCidBtn.addEventListener('click', pasteCID);
    elements.openBrowserBtn.addEventListener('click', openInBrowser);
    elements.downloadBtn.addEventListener('click', downloadFile);
}

// Helper function to make authenticated requests
async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (state.authToken) {
        headers['Authorization'] = `Bearer ${state.authToken}`;
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });
    
    // Check if unauthorized
    if (response.status === 401) {
        handleLogout();
        throw new Error('Session expired. Please login again.');
    }
    
    return response;
}

// Health check
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        updateStatus(elements.ipfsStatus, data.ipfs_connected);
        updateStatus(elements.solanaStatus, data.solana_connected);
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatus(elements.ipfsStatus, false);
        updateStatus(elements.solanaStatus, false);
    }
}

// Update status indicator
function updateStatus(element, isConnected) {
    const statusText = element.querySelector('.status-text');
    if (isConnected) {
        element.classList.add('connected');
        element.classList.remove('disconnected');
        statusText.textContent = 'Connected';
    } else {
        element.classList.add('disconnected');
        element.classList.remove('connected');
        statusText.textContent = 'Disconnected';
    }
}

// File selection using Tauri API
async function selectFile() {
    try {
        // Check if running in Tauri context (window.__TAURI_INTERNALS__ exists in Tauri v2)
        if (!window.__TAURI_INTERNALS__) {
            showResult(elements.uploadResult, 'error', 'Not a Desktop App', 
                'This application must be run as a desktop app using ./run.sh, not in a web browser. Please close the browser and run: ./run.sh');
            return;
        }
        
        // Use Tauri v2 dialog API - the correct way
        const { open } = window.__TAURI__.dialog;
        const selected = await open({
            multiple: false,
            directory: false,
            filters: [{
                name: 'All Files',
                extensions: ['pdf', 'txt', 'json', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3']
            }]
        });
        
        if (selected) {
            state.selectedFilePath = selected;
            elements.selectedFileName.textContent = selected.split('/').pop();
            elements.selectedFileName.classList.add('selected');
            elements.uploadBtn.disabled = false;
        }
    } catch (error) {
        console.error('File selection error:', error);
        showResult(elements.uploadResult, 'error', 'File Selection Error', error.message || String(error));
    }
}

// Upload file to IPFS
async function uploadFile() {
    if (!state.selectedFilePath) {
        showResult(elements.uploadResult, 'error', 'Error', 'Please select a file first');
        return;
    }
    
    setButtonLoading(elements.uploadBtn, true);
    
    try {
        const response = await apiRequest('/ipfs/upload', {
            method: 'POST',
            body: JSON.stringify({ file_path: state.selectedFilePath })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }
        
        state.lastCID = data.cid;
        elements.cidInput.value = data.cid;
        elements.registerBtn.disabled = false;
        
        showResult(elements.uploadResult, 'success', '✅ Upload Successful', 
            `File: ${data.filename}<br>
             CID: <code>${data.cid}</code><br>
             Size: ${formatBytes(data.size)}<br>
             <a href="${data.gateway_url}" target="_blank">View on Gateway</a>`
        );
    } catch (error) {
        showResult(elements.uploadResult, 'error', '❌ Upload Failed', error.message);
    } finally {
        setButtonLoading(elements.uploadBtn, false);
    }
}

// Toggle private key visibility
function toggleKeyVisibility() {
    const input = elements.privateKeyInput;
    if (input.type === 'password') {
        input.type = 'text';
        elements.toggleKeyBtn.textContent = 'Hide';
    } else {
        input.type = 'password';
        elements.toggleKeyBtn.textContent = 'Show';
    }
}

// Verify wallet
async function verifyWallet() {
    const privateKey = elements.privateKeyInput.value.trim();
    
    if (!privateKey) {
        showResult(elements.walletResult, 'error', 'Error', 'Please enter your private key');
        return;
    }
    
    setButtonLoading(elements.verifyWalletBtn, true);
    
    try {
        const response = await apiRequest('/solana/validate-wallet', {
            method: 'POST',
            body: JSON.stringify({ private_key: privateKey })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Validation failed');
        }
        
        state.isWalletVerified = true;
        elements.registerBtn.disabled = !state.lastCID;
        
        showResult(elements.walletResult, 'success', '✅ Wallet Verified', 
            `Balance: ${data.balance_sol.toFixed(6)} SOL<br>
             Network: ${data.network}<br>
             Public Key: ${data.public_key_preview}<br>
             Status: Connected`
        );
    } catch (error) {
        state.isWalletVerified = false;
        showResult(elements.walletResult, 'error', '❌ Validation Failed', error.message);
    } finally {
        setButtonLoading(elements.verifyWalletBtn, false);
    }
}

// Register on Solana
async function registerOnSolana() {
    const privateKey = elements.privateKeyInput.value.trim();
    const cid = state.lastCID || elements.cidInput.value.trim();
    
    if (!privateKey) {
        showResult(elements.walletResult, 'error', 'Error', 'Please enter your private key');
        return;
    }
    
    if (!cid) {
        showResult(elements.walletResult, 'error', 'Error', 'No CID available. Upload a file first.');
        return;
    }
    
    setButtonLoading(elements.registerBtn, true);
    
    try {
        const response = await apiRequest('/solana/register', {
            method: 'POST',
            body: JSON.stringify({ private_key: privateKey, cid: cid })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Registration failed');
        }
        
        // SECURITY: Clear private key from input after successful transaction
        elements.privateKeyInput.value = '';
        state.isWalletVerified = false;
        
        showResult(elements.walletResult, 'success', '✅ Transaction Successful', 
            `CID: <code>${data.cid}</code><br>
             Signature: <code>${data.signature.substring(0, 20)}...</code><br>
             Network: ${data.network}<br>
             <a href="${data.explorer_url}" target="_blank">View on Explorer</a><br>
             <small>Private key cleared from memory for security</small>`
        );
    } catch (error) {
        showResult(elements.walletResult, 'error', '❌ Transaction Failed', error.message);
    } finally {
        setButtonLoading(elements.registerBtn, false);
    }
}

// Paste last CID
function pasteCID() {
    if (state.lastCID) {
        elements.cidInput.value = state.lastCID;
        showResult(elements.accessResult, 'info', 'CID Pasted', `Using CID: ${state.lastCID}`);
        setTimeout(() => hideResult(elements.accessResult), 2000);
    } else {
        showResult(elements.accessResult, 'error', 'Error', 'No recent CID available');
    }
}

// Open in browser
async function openInBrowser() {
    const cid = elements.cidInput.value.trim();
    
    if (!cid) {
        showResult(elements.accessResult, 'error', 'Error', 'Please enter a CID');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/ipfs/gateway-url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cid: cid })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to get gateway URL');
        }
        
        // Check if running in Tauri context
        if (!window.__TAURI_INTERNALS__) {
            // Fallback for browser: open in new tab
            window.open(data.gateway_url, '_blank');
        } else {
            // Open URL using Tauri's shell plugin
            const { open } = window.__TAURI__.shell;
            await open(data.gateway_url);
        }
        
        showResult(elements.accessResult, 'success', '✅ Opening in Browser', 
            `CID: ${data.cid}<br>
             URL: <a href="${data.gateway_url}" target="_blank">${data.gateway_url}</a>`
        );
    } catch (error) {
        showResult(elements.accessResult, 'error', '❌ Error', error.message);
    }
}

// Download file
async function downloadFile() {
    const cid = elements.cidInput.value.trim();
    
    if (!cid) {
        showResult(elements.accessResult, 'error', 'Error', 'Please enter a CID');
        return;
    }
    
    // Check if running in Tauri context
    if (!window.__TAURI_INTERNALS__) {
        showResult(elements.accessResult, 'error', 'Not a Desktop App', 
            'Download requires desktop app. Please run: ./run.sh');
        return;
    }
    
    setButtonLoading(elements.downloadBtn, true);
    
    try {
        // Select download directory using Tauri dialog API
        const { open } = window.__TAURI__.dialog;
        const downloadDir = await open({
            directory: true,
            multiple: false
        });
        
        if (!downloadDir) {
            setButtonLoading(elements.downloadBtn, false);
            return;
        }
        
        const response = await apiRequest('/ipfs/download', {
            method: 'POST',
            body: JSON.stringify({ cid: cid, output_dir: downloadDir })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Download failed');
        }
        
        showResult(elements.accessResult, 'success', '✅ Download Successful', 
            `File: ${data.filename}<br>
             Location: ${data.path}<br>
             <a href="${data.gateway_url}" target="_blank">View on Gateway</a>`
        );
    } catch (error) {
        showResult(elements.accessResult, 'error', '❌ Download Failed', error.message);
    } finally {
        setButtonLoading(elements.downloadBtn, false);
    }
}

// Helper: Show result message
function showResult(element, type, title, message) {
    element.className = `result ${type} show`;
    element.innerHTML = `
        <div class="result-title">${title}</div>
        <div class="result-content">${message}</div>
    `;
}

// Helper: Hide result message
function hideResult(element) {
    element.classList.remove('show');
}

// Helper: Set button loading state
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '<span class="loading"></span> Processing...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

// Helper: Format bytes to human readable
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Clear sensitive data on window unload (security measure)
window.addEventListener('beforeunload', () => {
    // Clear private key from DOM if present
    if (elements.privateKeyInput) {
        elements.privateKeyInput.value = '';
    }
    // Note: We keep auth tokens for convenience, but in high-security 
    // scenarios you might want to clear them here too
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
