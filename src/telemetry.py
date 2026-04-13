import os
import json
import time
from datetime import datetime

USAGE_FILE = "usage_log.json"

def log_usage(provider, model, tokens):
    """Registra o uso de tokens localmente."""
    try:
        data = {}
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "r") as f:
                data = json.load(f)
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in data:
            data[today] = {}
        
        key = f"{provider}:{model}"
        if key not in data[today]:
            data[today][key] = 0
            
        data[today][key] += tokens
        
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"  [Telemetry] Erro ao logar uso: {e}")

# Controle de Cooldowns (Quota Hit)
_quota_cooldowns = {}

def set_quota_cooldown(provider: str, seconds: int = 60):
    """Marca um provedor como em cooldown (cota atingida)."""
    _quota_cooldowns[provider] = time.time() + seconds

def get_cooldown_remaining(provider: str) -> int:
    """Retorna segundos restantes de cooldown."""
    until = _quota_cooldowns.get(provider, 0)
    return max(0, int(until - time.time()))

def is_provider_ok(provider: str) -> bool:
    """Verifica se o provedor não está em cooldown."""
    return get_cooldown_remaining(provider) == 0

def get_daily_usage(provider=None):
    """Retorna o uso do dia atual."""
    try:
        if not os.path.exists(USAGE_FILE):
            return {}
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
        today = datetime.now().strftime("%Y-%m-%d")
        summary = data.get(today, {})
        
        if provider:
            return sum(v for k, v in summary.items() if k.startswith(provider))
        return summary
    except:
        return {}
