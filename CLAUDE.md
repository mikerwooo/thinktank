# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

The flagship product of [Autonomi](https://www.autonomi.dev/). Multi-agent autonomous startup system for Claude Code, OpenAI Codex CLI, and Google Gemini CLI. Takes PRD to fully deployed product with minimal human intervention.

## Commands

### Build
```bash
# Build dashboard frontend (required before release; writes to dashboard/static/ and dashboard-ui/dist/)
cd dashboard-ui && npm ci && npm run build:all && cd ..

# Build VSCode extension
cd vscode-extension && npm run compile && cd ..

# Build TypeScript SDK
cd sdk/typescript && npm run build && cd ..

# Watch mode for dashboard frontend (development)
cd dashboard-ui && npm run build:watch
```

### Test
```bash
# Full test suite (shell validation + Node.js unit tests + Python tests)
npm test

# Run a specific Node.js test file
node --test tests/protocols/a2a/some.test.js

# Run all tests in a subdirectory
node --test tests/protocols/*.test.js

# Dashboard-only tests
cd dashboard-ui && npm run test:all   # E2E + visual + parity
cd dashboard-ui && npm run test:e2e   # Playwright E2E only

# Python tests (memory system, dashboard API)
python3 -m pytest

# Shell script validation
bash -n autonomy/run.sh
bash -n autonomy/loki
bash tests/run-shellcheck.sh

# Benchmarks
./benchmarks/run-benchmarks.sh humaneval --execute --loki
./benchmarks/run-benchmarks.sh swebench --execute --loki
```

### Lint
```bash
cd vscode-extension && npm run lint
cd dashboard/frontend && npm run lint
```

### Run (Development)
```bash
# Dashboard API server (port 57374)
python3 dashboard/server.py

# Dashboard frontend dev server
cd dashboard/frontend && npm run dev

# VSCode extension watch mode
cd vscode-extension && npm run watch

# Run loki directly (after npm install -g loki-mode or local setup)
./autonomy/loki start ./prd.md
./autonomy/run.sh --provider codex ./prd.md
LOKI_PROVIDER=gemini ./autonomy/loki start ./prd.md
```

## Key Concepts

### RARV Cycle
Every iteration follows: **R**eason -> **A**ct -> **R**eflect -> **V**erify

### Model Selection
- **Opus**: Planning and architecture ONLY (system design, high-level decisions)
- **Sonnet**: Development and functional testing (implementation, integration tests)
- **Haiku**: Unit tests, monitoring, and simple tasks - use extensively for parallelization

### Multi-Provider Support (v5.0.0)
- **Claude Code**: Full features (subagents, parallel, Task tool, MCP)
- **OpenAI Codex CLI**: Degraded mode (sequential only, no Task tool)
- **Google Gemini CLI**: Degraded mode (sequential only, no Task tool)

```bash
# Provider selection
./autonomy/run.sh --provider codex ./prd.md
loki start --provider gemini ./prd.md
LOKI_PROVIDER=codex loki start ./prd.md
```

### Quality Gates
1. Shell syntax validation (bash -n, shellcheck)
2. Node.js unit tests + Python pytest suite
3. Mock/mutation detection (detect-mock-problems.sh, detect-test-mutations.sh)
4. 3-reviewer parallel system (blind review in run.sh)
5. Anti-sycophancy scoring (swarm/sycophancy.py - Jaccard similarity, verdict unanimity)
6. Severity-based blocking (Critical/High = BLOCK, returns non-zero)
7. Budget circuit breaker (creates .loki/PAUSE on overspend)
8. Policy engine enforcement (.loki/policies.json)
9. Test coverage gates (>80% unit, 100% pass)

CodeQL runs on push/PR to main and dev branches (.github/workflows/codeql.yml). ESLint runs only in vscode-extension and dashboard/frontend, not as a CI gate.

### Memory System (v5.43.0 - Complete Implementation)
- **Episodic**: Specific interaction traces (`.loki/memory/episodic/`)
- **Semantic**: Generalized patterns (`.loki/memory/semantic/`)
- **Procedural**: Learned skills (`.loki/memory/skills/`)
- **Progressive Disclosure**: 3-layer loading (index ~100 tokens, timeline ~500 tokens, full details)
- **Token Economics**: Discovery vs read token tracking with threshold-based actions
- **Vector Search**: Multi-provider embeddings (sentence-transformers, OpenAI, Cohere) with numpy cosine similarity fallback to TF-IDF
- **Consolidation**: 7-step pipeline (load, cluster, extract, merge, anti-pattern detect, Zettelkasten link, stats)
- **Namespace**: Auto-detects project identity from git/package.json for cross-project isolation
- **Unified Access**: Integrates retrieval with token economics (unified_access.py)
- **Knowledge Graph**: Cross-project pattern aggregation (knowledge_graph.py)
- **RAG Injector**: Context builder for prompt injection (rag_injector.py)
- **CLI**: `loki memory index|timeline|consolidate|economics|retrieve|episode|pattern|skill|vectors`
- **API**: REST endpoints at `/api/memory/*` (12 endpoints)
- **Implementation**: `memory/` Python package (~12,016 lines) with RARV integration

### Metrics System (ToolOrchestra-inspired)
- **Efficiency**: Task cost tracking (`.loki/metrics/efficiency/`)
- **Rewards**: Outcome/efficiency/preference signals (`.loki/metrics/rewards/`)

## Codebase Knowledge Graph (Quick Reference)

### Top-Level File Map

| File | Lines | Role |
|---|---|---|
| `autonomy/loki` | 12,089 | CLI (78 cmd_ functions, dispatch at line ~7768) |
| `autonomy/run.sh` | 9,604 | Orchestration engine (RARV loop) |
| `autonomy/completion-council.sh` | 1,403 | Completion detection (council voting) |
| `dashboard/server.py` | 4,635 | FastAPI (116 HTTP + 1 WebSocket endpoint) |
| `memory/retrieval.py` | 1,565 | Task-aware memory retrieval |
| `memory/storage.py` | 1,396 | File-based memory backend |
| `memory/engine.py` | 1,297 | Memory orchestrator |
| `memory/embeddings.py` | 1,330 | Multi-provider vector embeddings |
| `memory/consolidation.py` | 951 | Episodic-to-semantic 7-step pipeline |
| `memory/schemas.py` | 782 | Pydantic-like dataclass schemas |
| `memory/token_economics.py` | 631 | Token usage tracking and optimization |
| `memory/unified_access.py` | 591 | Retrieval + token economics integration |
| `memory/namespace.py` | 582 | Project namespace auto-detection |
| `memory/vector_index.py` | 459 | Pure numpy cosine similarity index |
| `mcp/server.py` | 1,439 | MCP server (13 tools, 3 resources, 2 prompts) |
| `providers/loader.sh` | 184 | Provider loader and auto-detection |

### Key Function Lookup

| Function | Location | Purpose |
|---|---|---|
| `cmd_start()` | `loki:489` | Start autonomous execution |
| `main()` (CLI) | `loki:7768` | CLI dispatch (case statement at 7779) |
| `main()` (runner) | `run.sh:9072` | Runner entry point |
| `run_autonomous()` | `run.sh:7982` | Main iteration loop |
| `build_prompt()` | `run.sh:7493` | Prompt construction |
| `save_state()` | `run.sh:7381` | Persist state |
| `council_should_stop()` | `completion-council.sh:1283` | Completion decision |
| `run_code_review()` | `run.sh:5474` | 3-reviewer blind code review |
| `create_checkpoint()` | `run.sh:6077` | Snapshot state (retains last 50) |
| `store_episode_trace()` | `run.sh:7220` | Memory storage bridge |
| `check_human_intervention()` | `run.sh:8735` | PAUSE/STOP/INPUT signals |
| `detect_complexity()` | `run.sh:1204` | Auto-detect project complexity |
| `get_rarv_tier()` | `run.sh:1333` | Map iteration to model tier |
| `get_rarv_phase_name()` | `run.sh:1357` | Map iteration mod 4 to RARV phase |
| `check_budget_limit()` | `run.sh:6719` | Budget circuit breaker |
| `is_rate_limited()` | `run.sh:6534` | Rate limit detection with backoff |

### Critical Data Flow

A PRD enters via `loki start` (line 489), which execs `run.sh`. The `run_autonomous()` loop (line 7982) builds prompts via `build_prompt()` (line 7493) injecting RARV instructions, SDLC phases, memory context, queue tasks, and checklist status. The provider is invoked (Claude via `-p` flag, Codex via `exec --full-auto` with `CODEX_MODEL_REASONING_EFFORT` env var, Gemini via positional prompt with `--approval-mode=yolo`). Post-iteration, the system runs checklist verification, app runner management, playwright smoke tests, and code review. Completion is determined by a council vote (`council_should_stop` at completion-council.sh:1283), completion promise text, or max iterations. All components communicate through `.loki/` filesystem state files.

See `.claude/projects/-Users-lokesh-git-loki-mode/memory/CODEBASE-KNOWLEDGE-GRAPH.md` for complete reference.

## Development Guidelines

### Feedback Loop Requirement (CRITICAL)

Before documenting ANY feature, installation method, or capability:

1. **Verify it exists** - Check files, run commands, test endpoints
2. **Run feedback loop** - Use Task tool with Opus to review claims for accuracy
3. **Be factual only** - Never document features that don't work yet
4. **Mark planned features** - Use "Coming Soon" or "Planned" labels for unimplemented features

**Example verification:**
```bash
# Before documenting "npm install -g loki-mode"
npm view loki-mode  # Does package exist on registry?

# Before documenting a CLI command
which loki && loki --help  # Does command exist?

# Before documenting a file path
ls -la path/to/file  # Does file exist?
```

**Feedback loop pattern:**
```
Task tool -> subagent_type: "general-purpose" or model: "opus"
Prompt: "Review the following claims for factual accuracy.
        Verify each statement is true and working.
        Flag anything that cannot be verified."
```

### Test and Resource Cleanup (MANDATORY - NEVER SKIP)

**Before reporting ANY task as done, run ALL cleanup steps below. No exceptions.**

1. **Kill spawned processes** (dashboard servers, test runners, etc.):
   ```bash
   lsof -ti:57374 | xargs kill -9 2>/dev/null || true
   pkill -f "loki-run-" 2>/dev/null || true
   ```

2. **Remove temp files**:
   ```bash
   rm -rf /tmp/loki-* /tmp/test-* /tmp/package /tmp/*.tgz 2>/dev/null || true
   ```

3. **Verify cleanup** (MUST run, not optional):
   ```bash
   ps -ef | grep -E "(loki|test)" | grep -v grep || echo "Clean"
   ls /tmp/loki-* /tmp/test-* 2>&1 | grep -v "No such file" || echo "Clean"
   ```

4. **Report cleanup status** to user in task completion message

### Git Commit Workflow (MANDATORY - FOLLOWS GLOBAL CLAUDE.md)

**When user says "commit" or "commit and push", follow this exact sequence:**

1. Run `git diff --stat` to show changed files
2. List each file with a 1-line description of the change
3. Suggest commit message in a code block
4. **STOP and WAIT for user approval** before executing `git commit`
5. Stage files individually by name (never `git add -A` or `git add .`)
6. Only after user confirms, commit and push if requested

### When Modifying SKILL.md
- Keep under 500 lines (currently ~266)
- Reference detailed docs in `references/` instead of inlining
- Update version in header AND footer
- Update CHANGELOG.md with new version entry

### Version Numbering
Follows semantic versioning: MAJOR.MINOR.PATCH
- Current: v6.12.5
- MAJOR bump for architecture changes (v6.0.0 = dual-mode architecture, loki run)
- MINOR bump for new features (v5.23.0 = Dashboard File-Based API)
- PATCH bump for fixes (v5.22.1 = session.json phantom state)

### Code Style
- **CRITICAL: NEVER use emojis** - Not in code, documentation, commit messages, README, or any output
- **No emoji exceptions** - This includes website content, markdown files, and all text
- If you see emojis anywhere in the codebase, remove them immediately
- Clear, concise comments only when necessary
- Follow existing patterns in codebase

## Release Workflow (CRITICAL - Follow Every Step)

When releasing a new version, follow ALL steps below. Nothing should be skipped.

### 1. Version Bump - ALL Files

Update the version string in every file listed below. Search for the old version and replace with the new one.

**Core version files (MUST update):**
```
VERSION                                  # Single line: X.Y.Z
package.json                             # "version": "X.Y.Z"
SKILL.md                                 # Header (line ~6) AND footer (last line)
Dockerfile                               # LABEL version="X.Y.Z"
Dockerfile.sandbox                       # LABEL version="X.Y.Z"
vscode-extension/package.json            # "version": "X.Y.Z"
CLAUDE.md                                # Version Numbering section (Current: vX.Y.Z)
```

**Module version files (MUST update):**
```
dashboard/__init__.py                    # __version__ = "X.Y.Z"
mcp/__init__.py                          # __version__ = "X.Y.Z"
```

**Documentation (MUST update):**
```
CHANGELOG.md                             # Add new version entry at top
docs/INSTALLATION.md                     # Version header (line ~5)
wiki/Home.md                             # Current Version line
wiki/_Sidebar.md                         # Version line
wiki/API-Reference.md                    # Example version in responses
```

**Docker image tags in docs (update on MAJOR/MINOR bumps):**
```
README.md                                # Docker example tags (lines ~81, ~380)
docs/INSTALLATION.md                     # Docker image tags (7+ occurrences)
docker-compose.yml                       # Version comment (line 1)
```

### 2. Build Dashboard Frontend

The dashboard frontend MUST be rebuilt before any release. The build script writes directly to both `dashboard-ui/dist/` and `dashboard/static/` -- no manual copy needed.

```bash
cd dashboard-ui && npm ci && npm run build:all && cd ..
```

Verify the built file exists and is reasonably sized (>100KB):
```bash
ls -la dashboard/static/index.html
```

**Note:** `npm publish` also runs `prepublishOnly` which triggers this build automatically. The CI workflows build it explicitly as well. The build-standalone.js script writes to both locations in a single step.

### 3. Run Tests

```bash
# E2E dashboard tests (requires dashboard running on port 57374)
cd dashboard-ui && npx playwright test && cd ..

# Shell script validation
bash -n autonomy/run.sh
bash -n autonomy/loki
```

### 4. Commit and Push

```bash
git add -A
git commit -m "release: vX.Y.Z - description"
git push origin main
```

**IMPORTANT:** Do NOT manually create tags. The GitHub Actions workflow automatically:
- Creates the git tag
- Creates the GitHub Release with artifacts
- Publishes to npm (includes `dashboard/static/index.html`)
- Builds and pushes Docker image (includes `dashboard/` with deps)
- Updates Homebrew tap
- Publishes VSCode extension (includes dashboard IIFE bundle)

### 5. Verify ALL Distribution Channels

```bash
# Watch workflow progress
gh run list --limit 1
gh run watch <run-id>

# npm - verify dashboard is included
npm view loki-mode version
npm pack loki-mode --dry-run 2>&1 | grep dashboard/static

# Docker - verify dashboard works
docker pull asklokesh/loki-mode:X.Y.Z
docker run --rm asklokesh/loki-mode:X.Y.Z loki version

# Homebrew
brew update && brew info loki-mode

# VSCode extension
# Check marketplace or: code --list-extensions --show-versions | grep loki

# GitHub Release
gh release view vX.Y.Z
```

### Distribution Channel Checklist

Every release MUST include these artifacts across ALL channels:

| Channel | Dashboard API (server.py) | Dashboard Frontend (static/) | Memory System | Skills/References |
|---------|--------------------------|------------------------------|---------------|-------------------|
| npm     | `dashboard/*.py`         | `dashboard/static/index.html`| `memory/`     | `skills/`, `references/` |
| Docker  | `COPY dashboard/`        | Built in Dockerfile or committed | `memory/` | `skills/`, `references/` |
| Homebrew| Full tarball             | Full tarball                 | Full tarball  | Full tarball |
| VSCode  | N/A (connects to API)    | `media/loki-dashboard.js` (IIFE bundle) | N/A | N/A |
| Release | Skill-only zip           | N/A                          | N/A           | `references/` |

### Credentials (GitHub Secrets)
All credentials are stored as GitHub repository secrets and used by the workflow:
- `NPM_TOKEN`: npm publish token
- `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`: Docker Hub credentials
- `HOMEBREW_TAP_TOKEN`: PAT for homebrew-tap updates

## Testing

```bash
# Run benchmarks
./benchmarks/run-benchmarks.sh humaneval --execute --loki
./benchmarks/run-benchmarks.sh swebench --execute --loki
```

## Research Foundation

Built on 2025 research from three major AI labs:

**OpenAI:**
- Agents SDK (guardrails, tripwires, handoffs, tracing)
- AGENTS.md / Agentic AI Foundation (AAIF) standards

**Google DeepMind:**
- SIMA 2 (self-improvement, hierarchical reasoning)
- Gemini Robotics (VLA models, planning)
- Dreamer 4 (world model training)
- Scalable Oversight via Debate

**Anthropic:**
- Constitutional AI (principles-based self-critique)
- Alignment Faking Detection (sleeper agent probes)
- Claude Code Best Practices (Explore-Plan-Code)

**Academic:**
- CONSENSAGENT (anti-sycophancy)
- GoalAct (hierarchical planning)
- A-Mem/MIRIX (memory systems)
- Multi-Agent Reflexion (MAR)
- NVIDIA ToolOrchestra (efficiency metrics)

See `references/openai-patterns.md`, `references/lab-research-patterns.md`, and `references/advanced-patterns.md`.
