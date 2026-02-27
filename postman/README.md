# Postman – FinanceAI Auth API

## Import the collection

1. Open Postman.
2. **Import** → **Upload Files** → select `FinanceAI_Auth.postman_collection.json`.
3. The collection **FinanceAI - Auth API** will appear.

## Variables

- **base_url** – Set to your server (e.g. `http://localhost:8000`). Edit at collection level.
- **access** / **refresh** – Filled automatically when you run **Register** or **Login** (see Tests script).

## Flow

1. Set `base_url` to `http://localhost:8000` (or your server).
2. Run **Register** to create a user (or **Login** if you already have one). Tokens are saved automatically.
3. Run **Get Profile**, **User Stats**, **User Activities**, or **Update Profile** – they use `Bearer {{access}}`.
4. **Logout** blacklists the refresh token (optional).

## Wallet endpoints

- **Wallet - Get Nonce**: Replace `0xYourEthereumAddress` in the URL with a real address.
- **Wallet - Verify**: Call after signing the nonce with your wallet; put the signature in the body.

For full API details, see `docs/API_AUTH.md`.
