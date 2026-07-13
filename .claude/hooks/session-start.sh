#!/bin/sh
# DeveloperOS SessionStart hook — inject the standard + orientation at the top of
# every session. Committed to .claude/settings.json, so it fires in BOTH local and
# cloud (claude.ai/code) sessions. A hook's stdout is added to the model's context
# at session start; this guarantees the session sees PROJECT.md (which, unlike
# CLAUDE.md, does NOT auto-load) and, locally, live re-entry state.
#
# Dependency-free on purpose: the rules/orientation payload never touches dos, so
# it can't fail on a machine (the cloud) that has no dos binary. The dos-resume
# payload is added only when dos is actually on PATH. See docs/NORTH-STAR.md.
#
# Self-naming: the project name is the repo folder name (which `dos new` makes
# equal to the Otto project name). So this is ONE identical file for every
# project — no per-project substitution — and the builder-kit ships it verbatim.

DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
# lowercased so a capital-cased clone (e.g. the cloud's "Developer-OS") still
# matches the Otto project name, which is always lowercase.
PROJECT_NAME=$(basename "$DIR" | tr '[:upper:]' '[:lower:]')

echo "== $PROJECT_NAME: session orientation =="
echo "Standing rules are in CLAUDE.md (already loaded). Before acting: read the"
echo "PROJECT.md below (especially Locations), confirm the next step still makes"
echo "sense, plan-first on anything non-trivial, and close the session with /wrap."
echo

if [ -f "${DIR}/PROJECT.md" ]; then
  echo "----- PROJECT.md -----"
  cat "${DIR}/PROJECT.md"
  echo "----- end PROJECT.md -----"
else
  echo "(no PROJECT.md yet — add one; it is this project's orientation + Locations)"
fi

# Local lane only: inject live re-entry state when dos + its registry are present.
# Cloud sessions set CLAUDE_CODE_REMOTE=true and have no dos binary — skip silently.
if [ "${CLAUDE_CODE_REMOTE}" != "true" ] && command -v dos >/dev/null 2>&1; then
  resume_out=$(dos resume "${PROJECT_NAME}" 2>/dev/null)
  if [ -n "${resume_out}" ]; then
    echo
    echo "----- dos resume ${PROJECT_NAME} -----"
    echo "${resume_out}"
    echo "----- end dos resume -----"
  fi
fi

exit 0
