#!/bin/bash

# Cleanup script for __pycache__ files in git
# This script removes all tracked __pycache__ files from git index

echo "=== Cleaning up __pycache__ files from git ==="

# Remove tracked __pycache__ directories from git index
echo "Removing tracked __pycache__ directories..."
git rm --cached -r dev_bot/__pycache__ tests/__pycache__ 2>/dev/null || echo "Some files may have already been removed"

# Check current status
echo ""
echo "=== Current git status ==="
git status --porcelain

# Verify no __pycache__ files are staged
echo ""
echo "=== Checking staged __pycache__ files ==="
git diff --cached --name-only | grep -E "__pycache__" && echo "WARNING: __pycache__ files still staged!" || echo "SUCCESS: No __pycache__ files staged"

echo ""
echo "=== Cleanup complete ==="
echo "Next steps:"
echo "1. Review the git status above"
echo "2. If everything looks good, commit the changes"
echo "3. Or use 'git reset' to undo if something is wrong"