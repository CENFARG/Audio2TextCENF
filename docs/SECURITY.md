# Seguridad — GROQ_API_KEY y rotación

## HC-01 — Gift key hardcodeada eliminada (v0.15.7)

**Problema:** `backend/config_manager.py` contenía `gift_key_encoded` hardcodeada (ofuscada Base64+XOR, trivialmente decodificable). Scanners de secretos (GitHub, TruffleHog) la detectan y el histórico de git la conserva.

**Estado en v0.15.7:** la key por defecto es placeholder vacío `""`. El histórico del tag `v0.15.6` conserva el valor viejo — NO se hizo `git filter-repo` automático (requiere decisión de equipo). Ver siguiente sección para rotación.

## Fuente primaria de GROQ_API_KEY (orden de prioridad)

1. **Variable de entorno `GROQ_API_KEY`** — ideal para CI, Docker, dev local. `export GROQ_API_KEY=gsk_...`
2. **OS keyring vault** (`python-keyring` si está instalado) — `keyring.set_password("audio2text-cenf", "groq_api_key", "gsk_...")`
3. **`config.json` `groq_api_key`** — fallback ofuscado al guardar (Base64+XOR). Compatible con instalaciones existentes.
4. **`gift_key_encoded` deprecated** — solo para compat, se migra automáticamente a `groq_api_key` si este está vacío, luego se limpia.

Si `python-keyring` no está instalado, se loggea `WARNING` y se usa env/config (no crashea).

## Uso

```python
from backend.config_manager import ConfigManager
cm = ConfigManager()
key = cm.get_groq_api_key()  # o cm.get_groq_api_key_from_env() (alias compat)
# Guardar con vault si disponible:
cm.set_groq_api_key("gsk_...", use_keyring=True)
```

```bash
# Env var (Windows PowerShell)
$env:GROQ_API_KEY="gsk_..."
# Env var (bash)
export GROQ_API_KEY="gsk_..."
# Keyring
pip install keyring
python -c "import keyring; keyring.set_password('audio2text-cenf','groq_api_key','gsk_...')"
```

## Rotación de la key comprometida

La key que estuvo hardcodeada en `v0.15.6` y anteriores debe considerarse **comprometida**:

1. Revocar en https://console.groq.com/keys (delete old key).
2. Crear nueva key en Groq Console.
3. Distribuir via canal seguro (no commit). Usuarios: `GROQ_API_KEY` env o keyring.
4. Opcional: limpiar histórico con `git filter-repo` **solo si el equipo lo aprueba** (reescribe historia, requiere force-push coordinado):
   ```bash
   git filter-repo --replace-text <(echo "gift_key_encoded==>REMOVED")
   # o --path backend/config_manager.py --invert-paths si se quiere purgar archivo
   ```
   **No ejecutar sin coordinar** — invalida clones y tags. Alternativa mínima: rotar key y dejar historia purgada a futuro (enfoque v0.15.7).

## .gitignore

- `config.json` y `.env` están ignorados (ver `.gitignore` líneas `config.json` y `.env`).
- **Nunca** commitear `config.json` con key real, ni `.env`.
- El build (`scripts/build_GENERAL_v2.py`) incluye `config/config.json` como `add-data` — es un template vacío, no la config del dev.

## Compatibilidad

- `_decode_gift_key` mantiene compat con configs viejas ofuscadas (plain `gsk_` pasa directo, Base64+XOR se decodifica).
- `get_groq_api_key_from_env()` es alias de `get_groq_api_key()` para no romper callers.

## Checklist pre-tag v0.15.7

- [x] `backend/config_manager.py` defaults vacíos
- [x] `rg -n "gsk_|gift_key" --hidden` no retorna secretos en working tree (verificar en CI)
- [x] `python -c "from backend.config_manager import ConfigManager; ..."` pasa
- [ ] Rotar key en Groq Console (manual, fuera del repo)
- [ ] (Opcional, equipo) `git filter-repo` si se decide purgar historia
