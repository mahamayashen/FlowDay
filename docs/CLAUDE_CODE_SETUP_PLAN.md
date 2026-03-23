# FlowDay — Claude Code Setup Plan (P3)

This document is your step-by-step guide to setting up Claude Code for the FlowDay project. Run these commands in your **local terminal** (not Cowork).

---

## Prerequisites

```bash
# Verify Claude Code is installed
claude --version

# Verify you're in the FlowDay repo
cd ~/path/to/FlowDay
git status
```

---

## Phase 1: Initialize Claude Code & Generate CLAUDE.md

### Step 1.1 — Run `/init` to see what Claude Code auto-detects

```bash
# Launch Claude Code in the project root
claude

# Inside the Claude Code REPL, run:
/init
```

**What to expect:** Claude Code scans the repo and generates a draft `CLAUDE.md`. Since we already have a comprehensive `CLAUDE.md`, compare its output against ours. Look for:
- Anything it detected that we missed (e.g., inferred patterns from existing code)
- Suggestions that conflict with our conventions — override them in CLAUDE.md

### Step 1.2 — Iterate on CLAUDE.md

After `/init`, review the diff:

```bash
git diff CLAUDE.md
```

If `/init` overwrote our CLAUDE.md, restore ours and cherry-pick any useful additions:

```bash
git checkout -- CLAUDE.md
# Then manually add any good suggestions from /init output
```

**Key things to verify in CLAUDE.md:**
- [ ] `@import claude-project-instructions.md` — brings in PRD context
- [ ] `@import docs/DATA_MODEL.md` — brings in data model reference
- [ ] Tech stack section matches the actual dependencies
- [ ] Architecture section covers monorepo layout, backend patterns, agent pipeline
- [ ] Coding conventions for both Python and TypeScript
- [ ] Testing strategy with specific frameworks and rules
- [ ] Do's and Don'ts are project-specific (not generic)

### Step 1.3 — Verify @import resolution

```bash
# Inside Claude Code REPL, ask it to confirm context:
> What files are imported via @import in CLAUDE.md? Summarize what you know about the data model.
```

Claude Code should reference both `claude-project-instructions.md` and `docs/DATA_MODEL.md` content. If it can't, check the @import paths are relative to project root.

---

## Phase 2: Configure Permissions

### Step 2.1 — Review `.claude/settings.json`

The permissions file is already created at `.claude/settings.json`. It uses allowlists for safe commands:

```bash
cat .claude/settings.json
```

**Allow list rationale:**
- **Dev tools:** `npm run *`, `pytest`, `ruff`, `mypy`, `alembic`, `docker compose` — safe dev commands
- **File ops:** `ls`, `cat`, `mkdir`, `cp`, `mv`, `find`, `grep` — read/explore the codebase
- **Git:** `git *` — version control (with destructive ops denied below)
- **Editors:** `Read`, `Write`, `Edit` — Claude Code's file tools

**Deny list rationale:**
- **Destructive:** `rm -rf /`, `sudo`, `chmod 777` — obvious safety
- **Pipe-to-bash:** `curl|bash`, `wget|bash` — arbitrary code execution
- **Git destructive:** `push --force`, `reset --hard` — protect git history
- **DB destructive:** `DROP DATABASE`, `DROP TABLE` — protect data

### Step 2.2 — Test permissions in Claude Code

```bash
# Inside Claude Code, verify allowed commands work:
> Run `ls -la` to see the project structure

# Verify denied commands are blocked:
> Run `sudo apt install something`
# Should be blocked by deny list
```

---

## Phase 3: Context Management Strategy

Claude Code has a finite context window. For a project this size, you need a strategy to keep Claude focused and fast.

### Strategy 1: `/clear` — Reset between unrelated tasks

```bash
# You just finished working on the Task model.
# Now you want to work on the AI agent pipeline.
# These are unrelated — clear context to avoid confusion.

/clear
```

**When to use `/clear`:**
- Switching between frontend and backend work
- Switching between different V1 features
- After a long debugging session (stale context hurts more than it helps)
- Before starting a new feature branch

### Strategy 2: `/compact` — Compress without losing thread

```bash
# You're deep into a long session implementing the weekly review pipeline.
# Context is getting full, but you don't want to lose the thread.

/compact
```

**When to use `/compact`:**
- Claude Code warns about context limits
- You're mid-task and `/clear` would lose important context
- After completing a sub-task within a larger feature
- The conversation has a lot of back-and-forth that can be summarized

### Strategy 3: `--continue` — Resume after a break

```bash
# You closed the terminal, had lunch, came back.
# Resume where you left off:

claude --continue
```

**When to use `--continue`:**
- Resuming work after closing the terminal
- Picking up where a previous session left off
- After a crash or disconnect

### Recommended workflow per feature

```
1. git checkout -b feature/<issue>-<name>
2. claude                         # start fresh session
3. > Describe the feature goal    # Claude has CLAUDE.md context automatically
4. ... work on the feature ...
5. /compact                       # if context gets heavy mid-feature
6. ... continue working ...
7. /clear                         # done with this feature
8. > Review my changes and suggest a commit message
9. git add -A && git commit
10. git push -u origin feature/<issue>-<name>
```

### Context budget tips

- **Don't paste entire files** into the chat — Claude Code can read them with `Read`. Say "read backend/agents/time_analyst.py" instead.
- **Be specific** about which agent/module you're working on — the CLAUDE.md Do's section reminds Claude to stay scoped.
- **Use @import wisely** — each imported file consumes context. We import the PRD and data model because they're referenced constantly. Don't import everything.
- **One feature per session** — if you're bouncing between auth and AI agents, `/clear` between them.

---

## Phase 4: Verification Checklist

Run these inside Claude Code to verify the setup is working:

```bash
# 1. Context check — does Claude know the project?
> What is FlowDay? What tech stack does it use?

# 2. Architecture check — does it understand the agent pipeline?
> Describe the multi-agent weekly review pipeline. Which agents run in parallel?

# 3. Conventions check — does it follow our rules?
> Write a sample FastAPI endpoint for creating a Task. Follow our project conventions.
# Verify: async, type hints, Pydantic schema (not ORM) as response, service layer

# 4. Scope check — does it flag V2 features?
> Should we add a natural language chat feature to the planner?
# Expected: Claude should flag this as V2 / out of scope

# 5. Testing check — does it know our test strategy?
> How should I test the Time Analyst agent?
# Expected: pytest-asyncio, Pydantic AI TestModel, structured output validation

# 6. Security check — does it remember security requirements?
> How should we store the user's Google OAuth token?
# Expected: Fernet encryption at rest, never plain text
```

---

## Quick Reference: Common Claude Code Commands

| Command | When to use |
|---------|-------------|
| `claude` | Start a new session |
| `claude --continue` | Resume last session |
| `/init` | (Re)generate CLAUDE.md from repo scan |
| `/clear` | Reset context (between unrelated tasks) |
| `/compact` | Compress context (mid-task, running low) |
| `claude --print "question"` | Quick one-shot question, no session |
| `claude commit` | Generate commit message from staged changes |

---

## Files Created in This Setup

```
FlowDay/
├── CLAUDE.md                        # Main Claude Code context file
├── claude-project-instructions.md   # V1 PRD (imported by CLAUDE.md)
├── .claude/
│   └── settings.json                # Permissions allowlist/denylist
├── docs/
│   ├── DATA_MODEL.md                # Data model reference (imported by CLAUDE.md)
│   └── CLAUDE_CODE_SETUP_PLAN.md    # This file
└── .gitignore
```
