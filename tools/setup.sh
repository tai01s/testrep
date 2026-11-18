#!/bin/bash
# Codex cloud setup script. In the environment settings, set the setup script to:  bash tools/setup.sh
# Needs these as Codex SECRETS (or environment variables):
#   FUTURELAB_KEY_1, FUTURELAB_KEY_2, FUTURELAB_KEY_3
# Optional: FUTURELAB_BASE_URL (default below), SCHOOL_PER_KEY (default 4)
set -e
BASE_URL="${FUTURELAB_BASE_URL:-https://futurelab.robo4you.at/v1}"

# Install location: system-wide if we can, else in the home folder.
if [ -w /usr/local/bin ] && mkdir -p /opt/school 2>/dev/null; then
  BIN=/usr/local/bin; HOMEDIR=/opt/school
else
  # Not admin: put `school` next to npm's global commands (already on the agent's PATH), else ~/.local/bin.
  NPMBIN="$(npm prefix -g 2>/dev/null)/bin"
  if [ -d "$NPMBIN" ] && [ -w "$NPMBIN" ]; then BIN="$NPMBIN"; else BIN="$HOME/.local/bin"; fi
  HOMEDIR="$HOME/.school"
  mkdir -p "$BIN" "$HOMEDIR"
  grep -q 'school-kit PATH' ~/.bashrc 2>/dev/null || echo "export PATH=\"$BIN:\$PATH\"  # school-kit PATH" >> ~/.bashrc
  export PATH="$BIN:$PATH"
fi

npm i -g opencode-ai@latest

# Secrets disappear before the agent starts, so save them to a file the wrapper reads.
umask 077
{
  echo "export FUTURELAB_BASE_URL=\"$BASE_URL\""
  for i in 1 2 3 4 5 6; do v="FUTURELAB_KEY_$i"; [ -n "${!v}" ] && echo "export $v=\"${!v}\""; done
} > "$HOMEDIR/env"
umask 022
case "$HOMEDIR" in "$HOME"/*) chmod 600 "$HOMEDIR/env" ;; *) chmod 644 "$HOMEDIR/env" ;; esac   # private when it lives in your home folder

cat > "$HOMEDIR/opencode.json" <<'JSON'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "futurelab": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "FutureLab (school)",
      "options": {
        "baseURL": "{env:FUTURELAB_BASE_URL}",
        "apiKey": "{env:FUTURELAB_API_KEY}"
      },
      "models": {
        "qwen3.8-flash-next": { "name": "Qwen 3.8 Flash Next" }
      }
    }
  }
}
JSON

cat > "$BIN/school" <<WRAP
#!/bin/bash
# Usage: school "<brief>"   (run from the folder holding the source files)
# Spreads runs over FUTURELAB_KEY_1..n, max \${SCHOOL_PER_KEY:-4} at once per key. Extra runs wait for a free slot.
. "$HOMEDIR/env"
export OPENCODE_CONFIG="$HOMEDIR/opencode.json"
# Keep repo/user skills and AGENTS-style instructions away from the school model (it got confused by them)
export OPENCODE_DISABLE_EXTERNAL_SKILLS=1 OPENCODE_DISABLE_CLAUDE_CODE=1
WRAP
cat >> "$BIN/school" <<'WRAP'
PER_KEY=${SCHOOL_PER_KEY:-4}
LOCKS=/tmp/school-slots; mkdir -p "$LOCKS"
keys=(); for i in 1 2 3 4 5 6; do v="FUTURELAB_KEY_$i"; [ -n "${!v}" ] && keys+=("$i"); done
[ ${#keys[@]} -eq 0 ] && { echo "school: no keys found (set FUTURELAB_KEY_1..3 as secrets and rerun setup)" >&2; exit 2; }
slot=""
while [ -z "$slot" ]; do
  for s in $(seq 1 $PER_KEY); do for k in "${keys[@]}"; do
    if mkdir "$LOCKS/k$k-s$s" 2>/dev/null; then slot="k$k-s$s"; key=$k; break 2; fi
  done; done
  [ -z "$slot" ] && sleep 2
done
trap 'rm -rf "$LOCKS/$slot"' EXIT INT TERM
v="FUTURELAB_KEY_$key"
export FUTURELAB_API_KEY="${!v}"
export XDG_DATA_HOME="/tmp/school-data/$slot"
mkdir -p "$XDG_DATA_HOME"
opencode run --agent plan -m futurelab/qwen3.8-flash-next ${SCHOOL_VARIANT:+--variant "$SCHOOL_VARIANT"} "$@" 2>&1 \
  | sed -E 's/\x1b\[[0-9;]*m//g' | sed -E '/^> plan · /d' | sed '/./,$!d'
exit ${PIPESTATUS[0]}
WRAP
chmod +x "$BIN/school"

# Also install the skill user-wide so Codex finds it from any folder.
SRC="$(cd "$(dirname "$0")/.." && pwd)/.agents/skills/delegate-to-school-model"
if [ -f "$SRC/SKILL.md" ]; then mkdir -p "$HOME/.agents/skills" && cp -r "$SRC" "$HOME/.agents/skills/"; echo "skill installed to ~/.agents/skills"; fi

# Warm-up while setup still has internet: downloads OpenCode's provider package and checks the keys.
echo "school installed at $BIN/school"
for l in /usr/local/bin "$HOME/.local/bin"; do [ "$BIN" != "$l" ] && [ -d "$l" ] && [ -w "$l" ] && ln -sf "$BIN/school" "$l/school"; done
echo "Warm-up call to the school model..."
if out=$(timeout 120 "$BIN/school" "Reply with exactly: OK" 2>&1); then
  echo "school model answered: $(echo "$out" | tail -1)"
else
  echo "WARNING: warm-up failed (setup continues): $(echo "$out" | tail -3)"
fi
