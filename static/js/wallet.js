/**
 * FinanceAI - Web3 wallet authentication (MetaMask / WalletConnect-style)
 * Connect wallet, sign nonce, verify with backend, receive JWT.
 */

const WALLET_NONCE_URL = '/api/auth/wallet/nonce/';
const WALLET_VERIFY_URL = '/api/auth/wallet/verify/';

/**
 * Generate and display QR code for wallet address login
 * @param {string} walletAddress - The wallet address (0x...)
 * @param {boolean} autoGenerate - If true, skips validation and generates immediately
 */
function generateWalletAddressQR(walletAddress, autoGenerate = false) {
    // Validate wallet address format (skip if auto-generating)
    if (!autoGenerate && (!walletAddress || !walletAddress.match(/^0x[a-fA-F0-9]{40}$/))) {
        alert('Invalid wallet address. Please enter a valid Ethereum address (0x...)');
        return;
    }
    
    // Create QR data - encode wallet address with a login prefix
    const qrData = `financeai://login/${walletAddress}`;
    
    // Generate QR code using Google Charts API (hardcoded)
    const qrContainer = document.getElementById('walletAddressQR');
    if (!qrContainer) return;
    
    const img = document.createElement('img');
    img.alt = 'Wallet Address QR Code';
    img.src = 'https://chart.googleapis.com/chart?cht=qr&chs=180x180&chld=M|0&chl=' + encodeURIComponent(qrData);
    img.style.width = '180px';
    img.style.height = '180px';
    img.style.borderRadius = '8px';
    
    qrContainer.innerHTML = '';
    qrContainer.appendChild(img);
    
    // Store the wallet address for later use
    window.currentWalletAddressQR = walletAddress;
    
    img.onerror = function() {
        qrContainer.textContent = 'Failed to generate QR code';
    };
}

/**
 * Copy QR wallet address data to clipboard
 */
function copyWalletQRData() {
    if (!window.currentWalletAddressQR) {
        alert('Please generate a QR code first');
        return;
    }
    const qrData = `financeai://login/${window.currentWalletAddressQR}`;
    navigator.clipboard.writeText(qrData).then(() => {
        const btn = document.getElementById('copyWalletBtn');
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = originalText; }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
}

/**
 * Check if a Web3 provider (e.g. MetaMask) is available.
 */
function hasWallet() {
    return typeof window !== 'undefined' && typeof window.ethereum !== 'undefined';
}

/**
 * Request wallet connection and return the first account address.
 * @returns {Promise<string|null>} Address or null if user denied.
 */
async function requestWalletAddress() {
    if (!hasWallet()) {
        return null;
    }
    try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        return accounts && accounts[0] ? accounts[0] : null;
    } catch (e) {
        console.warn('Wallet connect failed', e);
        return null;
    }
}

/**
 * Get current nonce for an address from the backend.
 * @param {string} address - Ethereum address (0x...)
 * @returns {Promise<string|null>} Nonce string or null.
 */
async function fetchWalletNonce(address) {
    const url = `${WALLET_NONCE_URL}?address=${encodeURIComponent(address)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === 'success' && data.data && data.data.nonce) {
        return data.data.nonce;
    }
    return null;
}

/**
 * Sign a message with the user's wallet (e.g. personal_sign).
 * @param {string} message - Plain text message to sign.
 * @param {string} address - Account address.
 * @returns {Promise<string|null>} Signature hex or null.
 */
async function signMessage(message, address) {
    if (!hasWallet()) return null;
    try {
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [message, address],
        });
        return signature;
    } catch (e) {
        console.warn('Sign failed', e);
        return null;
    }
}

/**
 * Verify signature with backend and return tokens + user.
 * @param {string} address
 * @param {string} signature
 * @returns {Promise<{access, refresh, user}|null>}
 */
async function verifyWalletSignature(address, signature) {
    const res = await fetch(WALLET_VERIFY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address, signature }),
        credentials: 'same-origin',
    });
    const data = await res.json();
    if (data.status === 'success' && data.data) {
        return data.data;
    }
    throw new Error(data.message || 'Verification failed');
}

/**
 * Full flow: connect wallet -> get nonce -> sign -> verify -> store tokens and redirect.
 * Call this when user clicks "Connect Wallet".
 * @param {Object} options - { onError: (msg) => {}, onStart: () => {} }
 * @returns {Promise<boolean>} True if login succeeded.
 */
async function connectWallet(options = {}) {
    const { onError = (msg) => alert(msg), onStart = () => {} } = options;

    if (!hasWallet()) {
        onError('No Web3 wallet found. Install MetaMask (https://metamask.io/download/) or another Web3 wallet, then refresh this page.');
        return false;
    }

    onStart();
    const address = await requestWalletAddress();
    if (!address) {
        onError('Wallet connection was denied or failed.');
        return false;
    }

    const nonce = await fetchWalletNonce(address);
    if (!nonce) {
        onError('Could not get sign-in challenge. Try again.');
        return false;
    }

    const signature = await signMessage(nonce, address);
    if (!signature) {
        onError('You need to sign the message in your wallet to continue.');
        return false;
    }

    let data;
    try {
        data = await verifyWalletSignature(address, signature);
    } catch (err) {
        onError(err.message || 'Sign-in verification failed. Please try again.');
        return false;
    }

    localStorage.setItem('token', data.access);
    localStorage.setItem('refresh', data.refresh || '');
    const user = data.user || {};
    const userForStorage = {
        id: user.id,
        name: user.name || user.username || `Wallet ${address.slice(0, 6)}...${address.slice(-4)}`,
        email: user.email || '',
        username: user.username,
        wallet_address: address,
    };
    localStorage.setItem('user', JSON.stringify(userForStorage));

    if (data.needs_username && typeof showSetUsernameModal === 'function') {
        showSetUsernameModal({
            title: 'Choose a display name',
            onSuccess: function() {
                if (typeof window !== 'undefined' && window.location) window.location.href = '/dashboard/';
            },
            onSkip: function() {
                if (typeof window !== 'undefined' && window.location) window.location.href = '/dashboard/';
            }
        });
        return true;
    }

    if (typeof window !== 'undefined' && window.location) {
        window.location.href = '/dashboard/';
    }
    return true;
}
