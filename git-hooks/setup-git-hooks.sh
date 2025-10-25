#!/bin/bash

set -e

ROOT_DIR="$(git rev-parse --show-toplevel)"
GIT_HOOKS_DIR="$ROOT_DIR/.git/hooks"
CUSTOM_HOOKS_DIR="$ROOT_DIR/git-hooks"

echo "🔧 Setting up Git hooks..."
echo ""

if [ ! -d "$GIT_HOOKS_DIR" ]; then
  echo "❌ Error: .git/hooks directory not found"
  echo "   Make sure you're running this from a Git repository"
  exit 1
fi

if [ ! -d "$CUSTOM_HOOKS_DIR" ]; then
  echo "❌ Error: git-hooks directory not found"
  echo "   Expected location: $CUSTOM_HOOKS_DIR"
  exit 1
fi

for hook in "$CUSTOM_HOOKS_DIR"/*; do
  if [ -f "$hook" ]; then
    hook_name=$(basename "$hook")
    target="$GIT_HOOKS_DIR/$hook_name"

    if [ -L "$target" ]; then
      echo "🔗 Updating symlink: $hook_name"
      rm "$target"
    elif [ -f "$target" ]; then
      echo "⚠️  Backing up existing hook: $hook_name -> $hook_name.backup"
      mv "$target" "$target.backup"
    fi

    echo "✅ Creating symlink for: $hook_name"
    ln -s "$hook" "$target"
    chmod +x "$hook"
  fi
done

echo ""
echo "✅ Git hooks setup complete!"
echo ""
echo "Installed hooks:"
for hook in "$CUSTOM_HOOKS_DIR"/*; do
  if [ -f "$hook" ]; then
    echo "  • $(basename "$hook")"
  fi
done
echo ""
