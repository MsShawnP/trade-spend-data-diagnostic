# Project Workflow

This project follows a phased development workflow. Each phase has a dedicated agent prompt in `.claude/agents/`. The human operator gates every phase transition — no phase runs automatically.

## Session Resumption

**On every session start or context compaction recovery, do this first:**

1. Check which workflow artifact files exist at project root: `PROJECT_PLAN.md`, `REVIEW_CODE.md`, `REVIEW_DATA.md`, `REVIEW_PROSE.md`, `REMEDIATION.md`, `AUDIT.md`
2. Read the most recent one to determine current state.
3. Tell the operator where they are. Examples:
   - No artifacts exist: "Starting fresh. Want me to run the planning agent?"
   - Only PROJECT_PLAN.md: "There's a plan in place. Are you still building, or ready for review?"
   - REMEDIATION.md exists with open items: "You're in remediation. REMEDIATION.md shows [n] blocking items remaining. Want to keep working on those?"
   - AUDIT.md exists with FAIL: "Last audit failed on [n] items. Want to loop back to remediation?"
   - AUDIT.md exists with PASS: "Audit passed. Ready to commit whenever you are."
4. Wait for the operator's direction before doing anything else.

**This applies after compaction too.** If you lose context mid-session, re-read the artifacts and reorient before continuing.

## Phases

### 1. PLAN
**Invoke:** "Run the planning agent" → spawns `.claude/agents/project-planner.md`
**Purpose:** Scope the project, inventory data sources and deliverables, define environment/dependencies, establish success criteria.
**Output:** `PROJECT_PLAN.md` at project root.
**Gate:** Operator reviews and approves the plan before implementation begins.

**Optional — Cross-model scope review:** After PROJECT_PLAN.md is produced, the operator can send it to a second model (e.g., Gemini) for an independent scope review. This catches planning blind spots that the same model that wrote the plan won't find. Not required, but recommended for complex or client-facing projects. The operator can paste the plan into another model and ask: "Review this project plan. What's missing, what's unrealistic, what are the risks I haven't considered?" Fold any useful feedback back into PROJECT_PLAN.md before proceeding.

### 2. BUILD
**No agent file.** This is normal implementation work in Claude Code. Build what the plan specifies.
**Gate:** Operator decides implementation is functionally complete and ready for review.

### 3. REVIEW — Code
**Invoke:** "Run code review" → spawns `.claude/agents/code-reviewer.md`
**Purpose:** Review all project code for quality, reproducibility, maintainability, and correctness.
**Output:** `REVIEW_CODE.md` at project root.

### 4. REVIEW — Data & Analysis
**Invoke:** "Run data review" → spawns `.claude/agents/data-science-reviewer.md`
**Purpose:** Validate analytical logic, metric definitions, join integrity, aggregation correctness, chart-data alignment, and statistical methods.
**Output:** `REVIEW_DATA.md` at project root.
**Note:** If this project has no data/analysis component, skip this phase.

### 5. REVIEW — Prose & Narrative
**Invoke:** "Run prose review" → spawns `.claude/agents/prose-reviewer.md`
**Purpose:** Review all written output — report narrative, dashboard labels, chart annotations, Excel tab descriptions, READMEs — for clarity, audience-appropriateness, and whether conclusions actually follow from the analysis.
**Output:** `REVIEW_PROSE.md` at project root.
**Note:** If this project has no written/narrative component (pure scripts, CLI tools), skip this phase.

### 6. REMEDIATE
**Invoke:** "Run remediation" → spawns `.claude/agents/remediation-tracker.md`
**Purpose:** Consolidate all findings from all review phases, prioritize, and track fixes.
**Output:** `REMEDIATION.md` at project root. Updated as issues are resolved.
**Gate:** Operator works through the remediation list. All blocking items must be resolved before audit.

### 7. AUDIT
**Invoke:** "Run final audit" → spawns `.claude/agents/final-auditor.md`
**Purpose:** Final quality gate. Verify deliverables match the plan, all remediation items are resolved, outputs render/run correctly.
**Output:** `AUDIT.md` at project root.
**Gate:** Operator reviews audit results. If clean, commit. If not, loop back to remediation.

## Scope Changes

If at any point during BUILD or later the operator needs to change the plan — add a deliverable, drop one, change a data source, adjust requirements — use this protocol:

1. **Operator says what's changing and why.**
2. **Update PROJECT_PLAN.md** directly. Add a `## Change Log` section at the bottom (or append to it if one already exists):
   ```
   ## Change Log
   - [date] Added Velocity Summary tab to Excel workbook — CEO needs this to replace a manual pivot table
   - [date] Dropped PDF deliverable — client confirmed HTML-only is fine
   - [date] Changed data source from CSV extract to direct SQLite query — performance issue with CSV at scale
   ```
3. **All subsequent reviews and audit check against the updated plan.** The change log ensures reviewers know what shifted and why, so they don't flag intentional changes as findings.
4. **Do not restart from scratch.** Scope changes are amendments, not rewrites. The plan evolves.

## Phase Transitions

**You must prompt the operator at every phase boundary.** Do not wait for them to remember the workflow — tell them where they are and what comes next.

### When to prompt

- **Session start:** Follow the Session Resumption protocol above.
- **After planning agent completes:** "Plan is in PROJECT_PLAN.md. Before we start building, I'd recommend sending it to Gemini for a scope review — paste the plan and ask what's missing, what's unrealistic, and what risks you haven't considered. Let me know when you've done that or if you want to skip it and go straight to build."
- **After the operator says something is "done," "finished," "ready," "working," or similar BUILD-completion language:** "Implementation sounds complete. The next step is code review. Want me to run it?"
- **After code review completes:** "Code review is done — findings are in REVIEW_CODE.md. Next up is the data & analysis review. Want me to run it?" (If the project has no data component: "No data/analysis component detected — skipping data review. Next is prose review. Want me to run it?")
- **After data review completes:** "Data review is done — findings are in REVIEW_DATA.md. Next is the prose & narrative review. Want me to run it?" (If no written/narrative component: "No narrative component detected — skipping prose review. Next is remediation. Want me to run it?")
- **After prose review completes:** "Prose review is done — findings are in REVIEW_PROSE.md. Next step is remediation to consolidate all findings into a single tracker. Want me to run it?"
- **After remediation is produced:** "Remediation tracker is in REMEDIATION.md. Here's the summary: [n] blocking, [n] advisory. Work through the blocking items and tell me when you're ready for me to update the tracker."
- **After operator signals remediation is done:** "Want me to update the remediation tracker to verify the fixes, or are you ready to go straight to final audit?"
- **After audit passes:** "Audit passed. Ready to commit."
- **After audit fails:** "Audit failed on [n] items. Here's what needs fixing: [summary]. Want me to loop back to remediation?"

### How to prompt

- One short sentence about what just happened.
- One short sentence about what's next.
- Ask if they want to proceed. Wait for the answer.
- **Do not auto-advance.** The operator may want to do manual work, take a break, or override the sequence.

## Workflow Rules

1. **The operator is the decision-maker.** Agents produce findings and recommendations. The operator decides what to act on and when to advance.
2. **Prompt at every boundary.** The operator should never have to remember what phase comes next — that's the workflow's job.
3. **Reorient after resumption.** On session start or compaction, re-read artifacts and tell the operator where they are before doing anything else.
4. **Phases are sequential.** Don't run code review before implementation is complete. Don't run audit before remediation.
5. **Reviews can be re-run.** After remediation, re-running a review agent is expected and encouraged.
6. **Scope changes are normal.** When the plan changes, update PROJECT_PLAN.md and keep going. Don't treat it as a failure.
7. **Phase outputs are project artifacts.** The .md files produced by each phase stay in the repo as documentation of the development process. Delete or .gitignore them based on your preference.
8. **Language-agnostic.** This workflow applies to R, Python, mixed-language, or non-code projects. Agents adapt their checks to whatever they find in the project.

## Project Context

When starting a new project, update this section with project-specific information:

- **Project name:**
- **Primary language(s):**
- **Data sources:**
- **Key deliverables:**
- **Environment notes:**
