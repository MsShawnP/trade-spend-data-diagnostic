# /wrap — End-of-session summary and handoff

Read PLAN.md, DECISIONS.md, HANDOFF.md, and FAILURES.md to understand full project context.

Review the current conversation and produce a comprehensive session wrap-up:

1. **Update HANDOFF.md** — Append a new section at the top (below the header) with:
   ```
   ## [YYYY-MM-DD] Session Wrap-Up
   **Session focus:** One-line summary of what this session was about
   **Completed:**
   - Bulleted list of what was accomplished
   **Current state:** Where the project stands now
   **Key files changed:**
   - List of files created or modified with brief descriptions
   **Next steps:**
   - Prioritized list of what to do next
   **Blockers:** Any outstanding issues (or "None")
   **Context for next session:** Anything the next session needs to know
   ```

2. **Update PLAN.md** — Mark completed tasks as done, add any new tasks discovered during the session, and adjust priorities if needed.

3. **Update FAILURES.md** — If anything failed or was abandoned during the session, document it.

4. **Summarize** — Print a brief summary to the console confirming what was updated.

This command is designed to make the next session (or the next person) productive immediately.
