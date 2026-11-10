#!/usr/bin/env bash
# scripts/publish-release.sh
# Publishes the v1.0.0 GitHub release with the 738 MB flashing package asset.

set -euo pipefail

TAG="v1.0.0"
TITLE="v1.0.0: EdgeML Jetson Nano Production OS (Track A)"
ARTIFACT="/home/piyush/edgeml-jetson-v1.0.0.tegraflash.tar.gz"
NOTES_FILE="docs/release-notes-v1.0.0.md"

# Ensure ~/.local/bin is in PATH for gh
export PATH="$HOME/.local/bin:$PATH"

if ! command -v gh >/dev/null 2>&1; then
    echo "[FAIL] gh CLI not found in PATH"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "=========================================================="
    echo " GitHub CLI authentication required"
    echo "=========================================================="
    echo "Please authenticate once by running:"
    echo "  gh auth login"
    echo "Select: GitHub.com -> HTTPS or SSH -> Browser or Token"
    echo "Then re-run this script: ./scripts/publish-release.sh"
    exit 1
fi

if [ ! -f "$ARTIFACT" ]; then
    echo "[FAIL] Release artifact not found at $ARTIFACT"
    exit 1
fi

echo "[INFO] Creating GitHub Release $TAG with 738 MB flashing archive..."
gh release create "$TAG" "$ARTIFACT#core-image-minimal-jetson-nano-devkit.tegraflash.tar.gz" \
    --title "$TITLE" \
    --notes-file "$NOTES_FILE"

echo ""
echo "[SUCCESS] Release $TAG published successfully to GitHub!"
echo "View release at: https://github.com/pengeon1/edgeml-jetson/releases/tag/$TAG"
