#!/bin/bash

echo "============================================"
echo "  ArchAnalyse - Startup"
echo "============================================"
echo ""
echo "How would you like to run ArchAnalyse?"
echo ""
echo "  [1] Auto-detect  (use GPU if available, otherwise CPU)"
echo "  [2] GPU only     (force GPU mode - requires NVIDIA CUDA)"
echo "  [3] CPU only     (force CPU mode)"
echo ""
read -p "Enter choice [1/2/3] (default: 1): " CHOICE

# Default to 1 if empty
CHOICE="${CHOICE:-1}"

case "$CHOICE" in
    1) MODE="auto" ;;
    2) MODE="gpu"  ;;
    3) MODE="cpu"  ;;
    *)
        echo "Invalid choice. Defaulting to auto-detect..."
        MODE="auto"
        ;;
esac

# ── Resolve auto-detect ───────────────────────────────────────────────────────
if [ "$MODE" = "auto" ]; then
    if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
        echo ""
        echo "GPU detected, building with CUDA support..."
        MODE="gpu"
    else
        echo ""
        echo "No GPU detected, building CPU only..."
        MODE="cpu"
    fi
fi

# ── GPU safety check ─────────────────────────────────────────────────────────
if [ "$MODE" = "gpu" ]; then
    if ! command -v nvidia-smi &> /dev/null || ! nvidia-smi &> /dev/null; then
        echo ""
        echo "WARNING: nvidia-smi not found or GPU not accessible."
        echo "         Make sure NVIDIA drivers and NVIDIA Container Toolkit are installed."
        echo ""
        read -p "Continue anyway? [y/N]: " CONFIRM
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
fi

# ── Clean up existing containers ─────────────────────────────────────────────
echo ""
echo "Stopping and removing existing containers..."
docker compose down 2>/dev/null || true

# ── Build & run ───────────────────────────────────────────────────────────────
if [ "$MODE" = "gpu" ]; then
    docker compose \
        -f docker-compose.yml \
        -f docker-compose.gpu.yml \
        build --build-arg USE_GPU=true
    docker compose \
        -f docker-compose.yml \
        -f docker-compose.gpu.yml \
        up -d
else
    docker compose build --build-arg USE_GPU=false
    docker compose up -d
fi

echo ""
echo "============================================"
echo "  ArchAnalyse is running!"
echo "  Open http://localhost in your browser."
echo "============================================"