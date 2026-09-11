# usage:  source ~/Desktop/Work/LLM-testing/scripts/use_model.sh evolving|deepseek|glm
# Points Claude Code at one Ark model for THIS shell only. Reads the key from .env
# (never prints it). Open a new terminal to go back to your normal Claude account.
if [ -n "${ZSH_VERSION:-}" ]; then _src=${(%):-%x}; else _src=${BASH_SOURCE[0]}; fi
_dir="$(cd "$(dirname "$_src")/.." && pwd)"
case "$1" in
  evolving) _model=doubao-seed-evolving;        _keyvar=ARK_KEY_EVOLVING ;;
  deepseek) _model=deepseek-v4-pro-ga-260813;   _keyvar=ARK_KEY_DEEPSEEK ;;
  glm)      _model=glm-5-2-260617;              _keyvar=ARK_KEY_GLM ;;
  *) echo "usage: source scripts/use_model.sh evolving|deepseek|glm"; return 1 2>/dev/null || exit 1 ;;
esac
_key="$(grep "^${_keyvar}=" "$_dir/.env" | cut -d= -f2-)"
if [ -z "$_key" ]; then echo "$_keyvar is empty in $_dir/.env"; return 1 2>/dev/null || exit 1; fi
export ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/compatible
export ANTHROPIC_AUTH_TOKEN="$_key"
export ANTHROPIC_MODEL="$_model" ANTHROPIC_DEFAULT_HAIKU_MODEL="$_model" \
       ANTHROPIC_DEFAULT_SONNET_MODEL="$_model" ANTHROPIC_DEFAULT_OPUS_MODEL="$_model" \
       CLAUDE_CODE_SUBAGENT_MODEL="$_model"
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
unset _src _dir _model _keyvar _key
echo "Claude Code -> $ANTHROPIC_MODEL via Ark (this shell only). Now run:  claude --effort high"
