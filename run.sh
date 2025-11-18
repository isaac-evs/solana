#!/bin/bash
# Launcher script for IPFS Solana Manager

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 IPFS Solana Manager - Launcher"
echo "================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if IPFS is running
echo "🔍 Checking IPFS daemon..."
if curl -s http://localhost:5001/api/v0/version > /dev/null 2>&1; then
    echo "✅ IPFS daemon is running"
else
    echo "⚠️  IPFS daemon is not running!"
    echo "Please start IPFS: 'ipfs daemon' or IPFS Desktop"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust/Cargo not found!"
    echo "Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo ""
echo "Starting services..."
echo ""

# Start frontend server in background
echo "🌐 Starting frontend server..."
python3 serve_frontend.py &
FRONTEND_PID=$!
sleep 2

# Start backend API server in background
echo "📡 Starting backend API server..."
source .venv/bin/activate
python backend/api_server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
    echo "❌ Backend failed to start!"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Backend running on http://127.0.0.1:8765"
echo ""

# Start Tauri application
echo "🎨 Starting Tauri application..."
cd src-tauri

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup EXIT INT TERM

# Run Tauri in development mode
cargo tauri dev

# Cleanup will run automatically when Tauri exits
