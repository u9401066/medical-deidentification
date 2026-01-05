#!/bin/bash
# Type checking script using ty (Astral's ultra-fast type checker)
# Usage: ./scripts/typecheck.sh [options]
#
# Options:
#   --strict    Run with all rules enabled (no ignores)
#   --quick     Quick check on main package only
#   --compare   Compare ty vs mypy performance

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

case "${1:-}" in
    --strict)
        echo "🔍 Running ty in strict mode..."
        ty check
        ;;
    --quick)
        echo "⚡ Quick type check on core/..."
        time ty check core/
        ;;
    --compare)
        echo "📊 Comparing ty vs mypy performance..."
        echo ""
        echo "=== ty (Astral) ==="
        time ty check 2>&1 | tail -3
        echo ""
        echo "=== mypy ==="
        time uv run mypy core/ --ignore-missing-imports 2>&1 | tail -3
        ;;
    *)
        echo "🚀 Running ty type checker..."
        echo ""
        time ty check
        echo ""
        echo "💡 Tips:"
        echo "   ty check --help     # See all options"
        echo "   ty server           # Start language server"
        ;;
esac
