# Script to remove secrets from git history
Set-Location "C:\Users\jalle\VSC\AvalokanGit\Avalokan"

# Abort any pending rebase
git rebase --abort 2>$null

# Create backup branch
git branch backup-before-history-rewrite 2>$null

# Create a new orphan branch (no history)
git checkout --orphan temp-clean-history

# Add all current files (which have env-based config)
git add -A

# Commit with a clean initial commit
git commit -m "Initial commit with env-based configuration"

# Delete old main and rename temp branch to main  
git branch -D main
git branch -m main

Write-Host "✓ Git history cleaned. Old history saved in 'backup-before-history-rewrite' branch."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review: git log --oneline"
Write-Host "  2. Force push: git push -f origin main"
