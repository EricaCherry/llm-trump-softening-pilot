"""
Shared harness: config/suite loading, model adapters, blind IDs, and I/O.
Used by run.py, grade.py, analyze.py. Standard library + pyyaml only.
"""
import json
import subprocess
import sys
import secrets
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- IO
def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        sys.exit(
            f"Config not found: {p}\n"
            "Copy config.example.yaml to config.yaml and fill it in."
        )
    return load_yaml(p)


def load_suite(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return load_yaml(p)


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def blind_id():
    return "r_" + secrets.token_hex(4)


def run_dir(config, kind):
    """kind in {'responses', 'grades'}"""
    return ROOT / kind / str(config.get("run_id", "pilot"))


# ----------------------------------------------------------------- clipboard
def to_clipboard(text):
    """Best-effort copy to the Windows clipboard. Silent no-op if unavailable."""
    try:
        subprocess.run("clip", input=text, text=True, check=True)
        return True
    except Exception:
        return False


# -------------------------------------------------------------- model adapters
def call_model(prompt_text, model_cfg, settings):
    adapter = "mock" if settings.get("mock") else model_cfg.get("adapter")
    if adapter == "mock":
        return _mock_model(prompt_text, model_cfg)
    if adapter == "manual":
        return _manual(prompt_text, model_cfg, settings)
    if adapter == "deepseek_api":
        return _api(prompt_text, model_cfg)
    if adapter == "cli":
        return _cli(prompt_text, model_cfg)
    raise ValueError(f"Unknown adapter: {adapter!r}")


def call_turn(user_text, history, model_cfg, settings, turn_label="", first_turn=True):
    """One turn of a multi-turn probe. `history` is prior [{role,content}, ...].
    For manual capture the app holds the history; for the API we pass it explicitly."""
    messages = list(history) + [{"role": "user", "content": user_text}]
    adapter = "mock" if settings.get("mock") else model_cfg.get("adapter")
    if adapter == "mock":
        return _mock_model(user_text, model_cfg)
    if adapter == "manual":
        if first_turn:
            note = (turn_label + "  START A NEW, EMPTY CHAT for this item.").strip()
        else:
            note = (turn_label + "  SAME chat as the previous turn - do NOT reset.").strip()
        return _manual(user_text, model_cfg, settings, turn_note=note)
    if adapter == "deepseek_api":
        return _api_chat(messages, model_cfg)
    if adapter == "cli":
        return _cli(user_text, model_cfg)
    raise ValueError(f"Unknown adapter: {adapter!r}")


def _mock_model(prompt_text, model_cfg):
    name = model_cfg.get("name", "mock")
    h = hashlib.sha1((name + prompt_text).encode()).hexdigest()[:6]
    return (
        f"[MOCK RESPONSE from {name}/{h}] This is placeholder text so you can "
        "exercise the run -> grade -> analyze pipeline without calling any real "
        "model. Replace by running with real adapters."
    )


def _manual(prompt_text, model_cfg, settings, turn_note=None):
    sentinel = settings.get("sentinel", "<<<END>>>")
    label = model_cfg.get("app_label", model_cfg.get("name", "model"))
    note = model_cfg.get("note", "")
    copied = to_clipboard(prompt_text)
    bar = "=" * 70
    print("\n" + bar)
    if turn_note:
        print("  >> " + turn_note)
    print(f"  PASTE INTO: {label}")
    if note:
        print(f"  REMINDER:   {note}")
    print(bar)
    print(prompt_text.rstrip())
    print(bar)
    if copied:
        print("  (prompt copied to clipboard - just paste it into the app)")
    print(f"  Paste the FULL response below. Finish with a line: {sentinel}")
    print(f"  Type SKIP then {sentinel} to skip this one.")
    print(bar)
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == sentinel:
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if text.upper().startswith("SKIP"):
        return None
    return text


def _http_post_json(url, headers, payload, timeout=120):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from None


def _api(prompt_text, cfg):
    return _api_chat([{"role": "user", "content": prompt_text}], cfg)


def _api_chat(messages, cfg):
    style = cfg.get("style", "openai")
    key = cfg.get("api_key", "")
    if not key or key.startswith("PASTE"):
        raise RuntimeError(
            f"Model '{cfg.get('name')}' has no valid api_key in config.yaml. "
            "The key shipped in deepseek.cmd is dead (401); paste a fresh one."
        )
    sys_prompt = cfg.get("system_prompt", "") or ""
    temp = cfg.get("temperature", 0)
    max_tokens = cfg.get("max_tokens", 1200)

    if style == "openai":
        url = cfg["base_url"].rstrip("/") + cfg.get("chat_path", "/v1/chat/completions")
        msgs = ([{"role": "system", "content": sys_prompt}] if sys_prompt else []) + list(messages)
        payload = {"model": cfg["model"], "messages": msgs,
                   "temperature": temp, "max_tokens": max_tokens}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        out = _http_post_json(url, headers, payload)
        return out["choices"][0]["message"]["content"]

    if style == "anthropic":
        url = cfg["base_url"].rstrip("/") + "/v1/messages"
        payload = {"model": cfg["model"], "max_tokens": max_tokens,
                   "temperature": temp, "messages": list(messages)}
        if sys_prompt:
            payload["system"] = sys_prompt
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
                   "Content-Type": "application/json"}
        out = _http_post_json(url, headers, payload)
        return out["content"][0]["text"]

    raise ValueError(f"Unknown api style: {style!r}")


def _cli(prompt_text, cfg):
    """Run a configurable CLI command. {prompt} in args is replaced; otherwise
    the prompt is piped to stdin. NOTE: agent CLIs (codex/claude) carry a coding
    system prompt and do NOT represent the chat apps - use only for an explicit
    'agent-mode' condition, never as a stand-in for ChatGPT/Claude.app."""
    cmd = cfg["command"]
    if any("{prompt}" in a for a in cmd):
        cmd = [a.replace("{prompt}", prompt_text) for a in cmd]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    else:
        proc = subprocess.run(cmd, input=prompt_text, capture_output=True,
                              text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"CLI failed ({proc.returncode}): {proc.stderr[:300]}")
    return proc.stdout.strip()
