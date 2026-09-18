#!/usr/bin/env bash
# Push the provider config from .env to Vercel, then deploy to production.
#
# Secrets are piped straight from .env into `vercel env add`, so no key is ever
# echoed to the terminal or stored in shell history. Run `vercel login` first —
# that step is interactive and cannot be scripted.
#
#   ./deploy.sh            # push env vars + deploy to production
#   ./deploy.sh --env-only # push env vars, skip the deploy
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "error: .env not found. Copy .env.example and add at least one provider key." >&2
  exit 1
fi

if ! vercel whoami >/dev/null 2>&1; then
  echo "error: not logged in to Vercel. Run 'vercel login' first (it is interactive)." >&2
  exit 1
fi

# Vars worth pushing. LLM_TIMEOUT is forced low for Vercel: the Hobby plan kills a
# function at 10s, and the app's 45s default would be cut off mid-request before
# the provider chain could fail over to the next one (build log #07).
push() {
  local name="$1" value="$2"
  [ -z "$value" ] && { echo "  skip  $name (not set in .env)"; return; }
  vercel env rm "$name" production --yes >/dev/null 2>&1 || true
  printf '%s' "$value" | vercel env add "$name" production >/dev/null
  echo "  set   $name"
}

read_env() {
  # Last assignment wins, quotes stripped, value never printed.
  sed -n "s/^$1=//p" .env | tail -1 | sed 's/^["'\'']//; s/["'\'']$//'
}

echo "Pushing environment to Vercel (production):"
push GEMINI_API_KEY "$(read_env GEMINI_API_KEY)"
push GROQ_API_KEY   "$(read_env GROQ_API_KEY)"
push LLM_PROVIDER   "$(read_env LLM_PROVIDER)"
push SITE_URL       "$(read_env SITE_URL)"
push LLM_TIMEOUT    "6"
push FLASK_DEBUG    "0"

if [ "${1:-}" = "--env-only" ]; then
  echo "Environment pushed. Skipping deploy."
  exit 0
fi

echo
echo "Deploying to production..."
vercel --prod
