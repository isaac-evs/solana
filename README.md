# IPFS Solana Manager

Modern desktop application for IPFS uploads and Solana blockchain transactions. Built with Tauri + Python backend.

## Features

- **Login System** - Simple authentication (default: admin/admin123)
- **IPFS Upload** - Upload files to IPFS with validation
- **Zip Downloads** - Downloads automatically zipped
- **Solana Integration** - Register CIDs on blockchain
- **Professional UI** - Proffesional and Polished UI design with Inter font
- **Security** - Protected routes, session management, input validation

## Quick Start

1. **Install Dependencies**
```bash
# Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# System dependencies (Linux)
sudo apt install libwebkit2gtk-4.0-dev libgtk-3-dev librsvg2-dev

# Tauri CLI
cargo install tauri-cli
```

2. **Start IPFS Daemon**
```bash
ipfs daemon
```

3. **Run Application**
```bash
./run.sh
```

**⚠️ IMPORTANT:** This is a **desktop application**, not a website!
- The Tauri window will open automatically
- **DO NOT** open `http://localhost:3000` in your browser
- If you see "undefined is not an object" errors, you're in a browser instead of the app

4. **Login**
- Username: `admin`
- Password: `admin123`

## Architecture

```
backend/          # Python Flask API
├── services/     # IPFS, Solana, Auth
├── utils/        # Security, logging
└── api_server.py # Main API

src/              # Frontend (HTML/CSS/JS)
src-tauri/        # Tauri desktop wrapper
```

## Configuration

- **API Server**: `http://127.0.0.1:8765`
- **Frontend**: `http://localhost:3000`
- **Solana**: Devnet
- **Data**: `~/.ipfs-solana-manager/`

## Security

- All endpoints require authentication
- 24-hour session tokens
- SHA-256 password hashing
- File validation (100MB limit)
- Downloads as zip files

## Development

```bash
# Run tests
python -m pytest

# Debug mode
FLASK_DEBUG=1 python backend/api_server.py

# Build for production
cd src-tauri && cargo tauri build
```

## License

MIT
