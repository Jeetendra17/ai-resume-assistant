<#
Push the provider config from .env to Vercel, then deploy to production.

PowerShell twin of deploy.sh, for terminals with no bash. It calls the Vercel CLI
by its full npm path, so it works even when the npm folder is missing from PATH.
Values are passed with --value inside this script, so no key is echoed to the
screen or written to your PowerShell history.

Run `vercel login` first -- that step is interactive and cannot be scripted:

  & "$env:APPDATA\npm\vercel.cmd" login
  powershell -ExecutionPolicy Bypass -File .\deploy.ps1            # push env + deploy
  powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -EnvOnly   # push env only
  powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -DryRun    # show plan, change nothing
#>
param(
    [switch]$EnvOnly,
    [switch]$DryRun
)

# Not "Stop": Windows PowerShell 5.1 turns every stderr line from a native
# command into a terminating error under Stop, and the Vercel CLI writes its
# ordinary progress output to stderr. Success is judged by $LASTEXITCODE instead.
$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

function Fail([string]$message) {
    Write-Host "error: $message" -ForegroundColor Red
    exit 1
}

# Find the CLI: the npm global bin first, then whatever PATH offers.
$vercel = Join-Path $env:APPDATA "npm\vercel.cmd"
if (-not (Test-Path $vercel)) {
    $cmd = Get-Command vercel -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        Fail "Vercel CLI not found. Install it with: npm i -g vercel"
    }
    $vercel = $cmd.Source
}

if (-not (Test-Path ".env")) {
    Fail ".env not found. Copy .env.example and add at least one provider key."
}

# Parse .env: last assignment wins, comments and blank lines skipped, quotes stripped.
$envVars = @{}
foreach ($line in Get-Content ".env") {
    if ($line -match '^\s*#' -or $line -notmatch '^\s*([A-Z_][A-Z0-9_]*)\s*=(.*)$') { continue }
    $envVars[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'")
}

# What to push. LLM_TIMEOUT is forced low: Vercel Hobby kills a function at 10s,
# and the app's 45s default would be cut off mid-request before the provider chain
# could fail over (build log #07). Keys are marked sensitive.
$plan = @(
    @{ Name = "GEMINI_API_KEY"; Value = $envVars["GEMINI_API_KEY"]; Sensitive = $true  },
    @{ Name = "GROQ_API_KEY";   Value = $envVars["GROQ_API_KEY"];   Sensitive = $true  },
    @{ Name = "LLM_PROVIDER";   Value = $envVars["LLM_PROVIDER"];   Sensitive = $false },
    @{ Name = "SITE_URL";       Value = $envVars["SITE_URL"];       Sensitive = $false },
    @{ Name = "LLM_TIMEOUT";    Value = "6";                        Sensitive = $false },
    @{ Name = "FLASK_DEBUG";    Value = "0";                        Sensitive = $false }
)

if (-not $DryRun) {
    & $vercel whoami *> $null
    if ($LASTEXITCODE -ne 0) {
        Fail "Not logged in to Vercel. Run: & `"$env:APPDATA\npm\vercel.cmd`" login"
    }
}

Write-Host "Pushing environment to Vercel (production):"
foreach ($item in $plan) {
    $name = $item.Name; $value = $item.Value
    if ([string]::IsNullOrEmpty($value)) {
        Write-Host ("  skip  {0,-16} (not set in .env)" -f $name)
        continue
    }
    $shown = if ($item.Sensitive) { "({0} chars)" -f $value.Length } else { "= $value" }
    if ($DryRun) {
        Write-Host ("  would set {0,-16} {1}" -f $name, $shown)
        continue
    }
    $cliArgs = @("env", "add", $name, "production", "--value", $value, "--force", "--yes")
    if ($item.Sensitive) { $cliArgs += "--sensitive" }
    & $vercel @cliArgs *> $null
    if ($LASTEXITCODE -ne 0) { Fail "Failed to set $name (exit $LASTEXITCODE)." }
    Write-Host ("  set   {0,-16} {1}" -f $name, $shown)
}

if ($DryRun) { Write-Host "`nDry run: nothing was changed."; exit 0 }
if ($EnvOnly) { Write-Host "`nEnvironment pushed. Skipping deploy."; exit 0 }

Write-Host "`nDeploying to production..."
& $vercel --prod 2>&1 | ForEach-Object { "$_" }
exit $LASTEXITCODE
