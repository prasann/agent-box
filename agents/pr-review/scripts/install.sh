#!/bin/bash
set -e

echo "🚀 Installing PR Review Agent..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed successfully"
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Install in development mode
echo "🔧 Installing pr-agent command..."
uv pip install -e .

echo "✅ Installation complete!"
echo ""
echo "To use pr-agent, run it with uv:"
echo "  uv run pr-agent --help"
echo "  uv run pr-agent review <pr-number>"
echo ""
echo "Or activate the virtual environment:"
echo "  source .venv/bin/activate"
echo "  pr-agent --help"
