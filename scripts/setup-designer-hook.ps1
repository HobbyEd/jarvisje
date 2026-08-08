# Installs the post-commit hook for the Software Designer Agent
$hookContent = @'
#!/bin/sh
# Sogyo Software Designer Agent - post-commit hook
# Runs after every local commit.

# Ensure the src package is importable when running from repo root
PYTHONPATH="src" python -m sogyo_chatbot.designer.cli || echo "Designer agent finished with warnings (non-blocking)"
'@

$hookPath = ".git/hooks/post-commit"
$hookContent | Set-Content -Path $hookPath -Encoding UTF8

Write-Host "Post-commit hook installed at $hookPath"
Write-Host "The Software Designer Agent will now run after every local commit."
