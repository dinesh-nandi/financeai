/**
 * FinanceAI - WalletConnect QR login
 * Scan QR with phone wallet (MetaMask, Trust, etc.) to sign in without a browser extension.
 * Uses WalletConnect Sign Client v2; requires WALLETCONNECT_PROJECT_ID in settings.
 */

const WALLET_NONCE_URL = '/api/auth/wallet/nonce/';
const WALLET_VERIFY_URL = '/api/auth/wallet/verify/';
const EIP155_CHAIN = 'eip155:1';

/**
 * Get WalletConnect project ID.
 * Prefer value injected by Django template; fall back to a local dev ID so QR login
 * works even if env loading is misconfigured.
 */
function getProjectId() {
    if (typeof window !== 'undefined') {
        const fromWindow = window.WALLETCONNECT_PROJECT_ID;
        if (fromWindow && String(fromWindow).trim() !== '') {
            return String(fromWindow).trim();
        }
    }
    // Fallback: hardcoded project ID from .env.example for local development.
    // Replace with your own from https://cloud.walletconnect.com/ if needed.
    return 'c87b1435be932481efaf221b253fa5ce';
}

/**
 * Show the QR modal with the given URI and status text.
 */
function showQRModal(uri, statusText, onClose) {
    const existing = document.getElementById('wc-qr-modal');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'wc-qr-modal';
    overlay.className = 'wc-qr-modal-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-label', 'Connect with QR code');

    const box = document.createElement('div');
    box.className = 'wc-qr-modal-box';

    const title = document.createElement('h3');
    title.className = 'wc-qr-modal-title';
    title.textContent = 'Sign in with your phone wallet';

    const status = document.createElement('p');
    status.className = 'wc-qr-modal-status';
    status.textContent = statusText;

    const qrContainer = document.createElement('div');
    qrContainer.className = 'wc-qr-container';
    qrContainer.id = 'wc-qr-code';

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'wc-qr-modal-close';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => {
        if (typeof onClose === 'function') onClose();
        overlay.remove();
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            if (typeof onClose === 'function') onClose();
            overlay.remove();
        }
    });

    box.appendChild(closeBtn);
    box.appendChild(title);
    box.appendChild(status);
    box.appendChild(qrContainer);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    return { overlay, statusEl: status, qrContainer };
}

/**
 * Render QR code image from URI.
 * Uses Google Chart API to generate a PNG QR (no extra JS dependencies),
 * so it reliably shows a visible black-and-white QR image.
 */
function renderQR(element, uri) {
    if (!element || !uri) return;
    const img = document.createElement('img');
    img.alt = 'WalletConnect QR code';
    img.src =
        'https://chart.googleapis.com/chart?cht=qr&chs=260x260&chld=M|0&chl=' +
        encodeURIComponent(uri);
    img.className = 'wc-qr-image';
    element.innerHTML = '';
    element.appendChild(img);
    // Fallback: if image fails to load (network blocked), show copyable link instead
    img.onerror = function () {
        element.innerHTML = '';
        const msg = document.createElement('p');
        msg.textContent = 'QR image could not be loaded on this network. You can still connect by copying the WalletConnect link into your phone wallet.';
        msg.style.fontSize = '12px';
        msg.style.color = 'var(--text-secondary)';
        msg.style.marginBottom = '8px';

        const input = document.createElement('textarea');
        input.value = uri;
        input.readOnly = true;
        input.style.width = '100%';
        input.style.height = '80px';
        input.style.fontSize = '11px';
        input.style.padding = '8px';
        input.style.borderRadius = '8px';
        input.style.border = '1px solid var(--border-color)';
        input.style.background = 'var(--bg-secondary)';
        input.style.color = 'var(--text-primary)';

        element.appendChild(msg);
        element.appendChild(input);
    };
}

/**
 * Close the QR modal by ID.
 */
function closeQRModal() {
    const modal = document.getElementById('wc-qr-modal');
    if (modal) modal.remove();
}

/**
 * Connect via WalletConnect QR: show QR, wait for session, get nonce, sign, verify, then redirect.
 * @param {Object} options - { onError: (msg) => {}, onStart: () => {}, onStatus: (msg) => {} }
 * @returns {Promise<boolean>}
 */
async function connectWalletViaQR(options = {}) {
    const {
        onError = (msg) => alert(msg),
        onStart = () => {},
        onStatus = () => {},
    } = options;

    const projectId = getProjectId();

    onStart();
    let abort = false;
    const { overlay, statusEl, qrContainer } = showQRModal('', 'Preparing QR code…', () => { abort = true; });

    try {
        // Use a known good version of WalletConnect Sign Client from esm.sh
        const SignClient = (await import('https://esm.sh/@walletconnect/sign-client@2.21.2')).default;
        const client = await SignClient.init({ projectId });

        const { uri, approval } = await client.connect({
            requiredNamespaces: {
                eip155: {
                    chains: [EIP155_CHAIN],
                    methods: ['personal_sign', 'eth_sign'],
                    events: [],
                },
            },
        });

        if (abort) return false;

        if (!uri) {
            closeQRModal();
            onError('Could not generate connection link.');
            return false;
        }

        statusEl.textContent = 'Scan with your phone wallet (MetaMask, Trust Wallet, etc.)';
        renderQR(qrContainer, uri);

        const session = await approval();
        if (abort) return false;

        const accounts = session?.namespaces?.eip155?.accounts;
        if (!accounts || accounts.length === 0) {
            closeQRModal();
            onError('No account received from wallet.');
            return false;
        }

        const accountId = accounts[0];
        const address = accountId.includes(':') ? accountId.split(':')[2] : accountId;
        if (!address || !address.startsWith('0x')) {
            closeQRModal();
            onError('Invalid account from wallet.');
            return false;
        }

        onStatus('Requesting sign-in challenge…');
        const nonceRes = await fetch(`${WALLET_NONCE_URL}?address=${encodeURIComponent(address)}`);
        const nonceData = await nonceRes.json();
        const nonce = nonceData?.data?.nonce;
        if (!nonce) {
            closeQRModal();
            onError(nonceData?.message || 'Could not get sign-in challenge.');
            return false;
        }

        onStatus('Approve the sign-in request in your wallet…');
        const signature = await client.request({
            topic: session.topic,
            chainId: EIP155_CHAIN,
            request: {
                method: 'personal_sign',
                params: [nonce, address],
            },
        });

        if (abort) return false;
        if (!signature || typeof signature !== 'string') {
            closeQRModal();
            onError('Signature was not received.');
            return false;
        }

        onStatus('Verifying…');
        const verifyRes = await fetch(WALLET_VERIFY_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, signature }),
        });
        const verifyData = await verifyRes.json();
        closeQRModal();

        if (verifyData.status !== 'success' || !verifyData.data) {
            onError(verifyData.message || 'Sign-in verification failed.');
            return false;
        }

        const data = verifyData.data;
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
    } catch (e) {
        if (!abort) closeQRModal();
        console.warn('WalletConnect QR error', e);
        onError(e?.message || 'QR login failed. Try again or use email / extension.');
        return false;
    }
}

function initQRButton() {
    const qrBtn = document.getElementById('connect-qr-btn');
    if (!qrBtn) return;
    qrBtn.addEventListener('click', function () {
        const qrText = document.getElementById('qr-btn-text');
        const qrSpinner = document.getElementById('qr-spinner');
        const errorMessage = document.getElementById('error-message');
        connectWalletViaQR({
            onStart: function () {
                if (errorMessage) {
                    errorMessage.classList.remove('show');
                    errorMessage.textContent = '';
                }
                if (qrText) qrText.textContent = 'Opening QR…';
                if (qrSpinner) qrSpinner.classList.remove('hidden');
            },
            onStatus: function (msg) {
                if (qrText) qrText.textContent = msg || 'Sign in with QR code';
            },
            onError: function (msg) {
                if (errorMessage) {
                    errorMessage.textContent = msg;
                    errorMessage.classList.add('show');
                }
                if (qrText) qrText.textContent = 'Sign in with QR code';
                if (qrSpinner) qrSpinner.classList.add('hidden');
            },
        }).then(function (ok) {
            if (!ok && qrText) qrText.textContent = 'Sign in with QR code';
            if (!ok && qrSpinner) qrSpinner.classList.add('hidden');
        });
    });
}

if (typeof window !== 'undefined') {
    window.connectWalletViaQR = connectWalletViaQR;
    window.closeQRModal = closeQRModal;
    window.hasWalletConnectQR = function () {
        const id = getProjectId();
        return !!id && id.trim() !== '';
    };
    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initQRButton);
        } else {
            initQRButton();
        }
    }
}
