"""Pluggable LLM backends, free tiers first.

Most hosted inference APIs (Groq, OpenRouter, Cerebras, Mistral, Together, Ollama,
OpenAI) speak the same OpenAI `/chat/completions` shape, so they share one adapter and
differ only in base URL, default model and env var. Gemini and Anthropic get their own
adapters because their wire formats differ.

Nothing here is required: with no keys set at all the app falls back to extractive
answers from the local resume index, so a deployment never breaks.
"""

import json
import os
import urllib.error
import urllib.request

TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "45"))

# urllib's default User-Agent ("Python-urllib/3.x") is rejected by Cloudflare in
# front of several provider APIs -- Groq returns HTTP 403 "error code: 1010"
# before the request ever reaches them. Any ordinary UA string gets through.
USER_AGENT = "jeetendra-portfolio/1.0 (+https://github.com/Jeetendra17/ai-resume-assistant)"


class ProviderError(RuntimeError):
    pass


def _post_json(url, payload, headers, timeout=TIMEOUT):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", USER_AGENT)
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise ProviderError(f"HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise ProviderError(str(exc)) from exc


class Provider:
    """Base class. `name` is what shows up in the UI badge."""

    name = "provider"
    label = "Provider"
    free = False
    env_key = ""
    default_model = ""
    signup = ""

    def __init__(self):
        self.api_key = os.environ.get(self.env_key, "").strip() if self.env_key else ""
        self.model = os.environ.get(f"{self.name.upper()}_MODEL", "") or self.default_model

    def available(self):
        return bool(self.api_key)

    def complete(self, system, messages):
        raise NotImplementedError


class OpenAICompatible(Provider):
    """Shared adapter for every `/chat/completions` API."""

    base_url = ""
    extra_headers = {}

    def complete(self, system, messages):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + messages,
            "max_tokens": int(os.environ.get("ASSISTANT_MAX_TOKENS", "800")),
            "temperature": 0.3,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", **self.extra_headers}
        data = _post_json(f"{self.base_url}/chat/completions", payload, headers)
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise ProviderError(f"unexpected response shape: {str(data)[:200]}") from exc


class Groq(OpenAICompatible):
    name = "groq"
    label = "Groq"
    free = True
    env_key = "GROQ_API_KEY"
    base_url = "https://api.groq.com/openai/v1"
    default_model = "llama-3.3-70b-versatile"
    signup = "https://console.groq.com/keys"


class OpenRouter(OpenAICompatible):
    name = "openrouter"
    label = "OpenRouter"
    free = True
    env_key = "OPENROUTER_API_KEY"
    base_url = "https://openrouter.ai/api/v1"
    # `:free` models cost nothing but are rate limited and occasionally busy.
    default_model = "meta-llama/llama-3.3-70b-instruct:free"
    signup = "https://openrouter.ai/keys"

    @property
    def extra_headers(self):
        return {
            "HTTP-Referer": os.environ.get("SITE_URL", "http://localhost:5000"),
            "X-Title": "Jeetendra Kumar Patel - Portfolio",
        }


class Cerebras(OpenAICompatible):
    name = "cerebras"
    label = "Cerebras"
    free = True
    env_key = "CEREBRAS_API_KEY"
    base_url = "https://api.cerebras.ai/v1"
    default_model = "llama-3.3-70b"
    signup = "https://cloud.cerebras.ai"


class Mistral(OpenAICompatible):
    name = "mistral"
    label = "Mistral"
    free = True
    env_key = "MISTRAL_API_KEY"
    base_url = "https://api.mistral.ai/v1"
    default_model = "mistral-small-latest"
    signup = "https://console.mistral.ai/api-keys"


class Together(OpenAICompatible):
    name = "together"
    label = "Together AI"
    free = True
    env_key = "TOGETHER_API_KEY"
    base_url = "https://api.together.xyz/v1"
    default_model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
    signup = "https://api.together.ai/settings/api-keys"


class Ollama(OpenAICompatible):
    """Fully local and fully free -- useful for development, not for the hosted site."""

    name = "ollama"
    label = "Ollama (local)"
    free = True
    env_key = ""
    default_model = "llama3.1:8b"
    signup = "https://ollama.com"

    def __init__(self):
        super().__init__()
        self.base_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/v1")
        self.api_key = "ollama"  # Ollama ignores the value but the header must exist.

    def available(self):
        return os.environ.get("USE_OLLAMA", "").lower() in ("1", "true", "yes")


class OpenAI(OpenAICompatible):
    name = "openai"
    label = "OpenAI"
    env_key = "OPENAI_API_KEY"
    base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o-mini"
    signup = "https://platform.openai.com/api-keys"


class Gemini(Provider):
    """Google's free tier -- native REST shape, not OpenAI-compatible."""

    name = "gemini"
    label = "Google Gemini"
    free = True
    env_key = "GEMINI_API_KEY"
    default_model = "gemini-2.0-flash"
    signup = "https://aistudio.google.com/apikey"

    def complete(self, system, messages):
        contents = [
            {
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
        ]
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": int(os.environ.get("ASSISTANT_MAX_TOKENS", "800")),
            },
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        data = _post_json(url, payload, {"x-goog-api-key": self.api_key})
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"unexpected response shape: {str(data)[:200]}") from exc


class Anthropic(Provider):
    """Uses the official SDK rather than raw HTTP, per Anthropic's guidance."""

    name = "anthropic"
    label = "Anthropic Claude"
    env_key = "ANTHROPIC_API_KEY"
    default_model = "claude-opus-4-8"
    signup = "https://console.anthropic.com/settings/keys"

    def complete(self, system, messages):
        try:
            import anthropic as anthropic_sdk
        except ImportError as exc:
            raise ProviderError("anthropic package not installed") from exc
        try:
            client = anthropic_sdk.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=int(os.environ.get("ASSISTANT_MAX_TOKENS", "800")),
                system=[
                    {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
                ],
                messages=messages,
            )
        except Exception as exc:
            raise ProviderError(str(exc)) from exc
        if response.stop_reason == "refusal":
            raise ProviderError("refused")
        return "".join(b.text for b in response.content if b.type == "text").strip()


# Ordered cheapest-and-freest first. The chain walks this list and uses the first
# provider that is configured and actually responds.
ALL_PROVIDERS = [
    Groq,
    Gemini,
    Cerebras,
    OpenRouter,
    Mistral,
    Together,
    Ollama,
    Anthropic,
    OpenAI,
]

_BY_NAME = {p.name: p for p in ALL_PROVIDERS}


def resolve_chain():
    """Build the ordered list of usable providers.

    `LLM_PROVIDER` pins a specific one (or a comma-separated preference order);
    otherwise every configured provider is tried in free-first order.
    """
    preferred = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if preferred:
        order = [_BY_NAME[n] for n in (x.strip() for x in preferred.split(",")) if n in _BY_NAME]
    else:
        order = ALL_PROVIDERS

    chain = []
    for cls in order:
        provider = cls()
        if provider.available():
            chain.append(provider)
    return chain


def catalog():
    """Metadata for docs and the setup panel -- no secrets included."""
    return [
        {
            "name": p.name,
            "label": p.label,
            "free": p.free,
            "env_key": p.env_key,
            "default_model": p.default_model,
            "signup": p.signup,
        }
        for p in (cls() for cls in ALL_PROVIDERS)
    ]
