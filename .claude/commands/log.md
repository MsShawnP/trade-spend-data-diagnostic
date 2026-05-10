# /log — Append a decision or progress entry

Read PLAN.md to understand current goals and phase.
Read DECISIONS.md and HANDOFF.md for existing context.

Based on the conversation so far, append a timestamped entry to the appropriate file:

- If this is a **design or technical decision**, append to DECISIONS.md using this format:
  ```
  ## [YYYY-MM-DD] Decision Title
  **Context:** Why this came up
  **Decision:** What was decided
  **Alternatives considered:** What else was evaluated
  **Consequences:** What this means going forward
  ```

- If this is a **progress update or status change**, append to HANDOFF.md using this format:
  ```
  ## [YYYY-MM-DD] Status Update
  **Completed:** What was done
  **Current state:** Where things stand
  **Next steps:** What should happen next
  **Blockers:** Any issues (or "None")
  ```

- If this is a **failure or lesson learned**, append to FAILURES.md using this format:
  ```
  ## [YYYY-MM-DD] What Failed
  **What happened:** Description of the failure
  **Why it failed:** Root cause
  **What we learned:** Takeaway for future work
  **Action items:** What to change going forward
  ```

After appending, briefly confirm what was logged and where.
