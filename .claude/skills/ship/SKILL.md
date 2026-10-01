---
name: ship
description: Commit, push and open the PR for the branch Claude last reported as ready for review.
disable-model-invocation: true
---

Invoking `/ship` is the user's confirmation under CLAUDE.md **Review before commit**: land the branch from your latest review report, following CLAUDE.md **Landing a branch**.

1. **Locate.** Go to the worktree named in your latest report and run `git status`. Ask before going further when:
   - no report in this session proposed a commit;
   - the branch is `main` or the active phase branch;
   - the working tree differs from the report (the user may have edited files while reviewing): list the differences and ask whether to include them;
   - the report asked about ticking a `ROADMAP.md` checkbox and the user hasn't answered.

   Done when the files to commit and the message are settled.
2. **Commit.** Stage the files by name and commit with the report's proposed subject and body, ending with the attribution line from the current system reminder.
   - A hook that rewrites files (ruff) means the commit did not happen: re-stage those files and commit again.
   - A hook that fails without rewriting (pyright) blocks the ship: report the error and stop. Hooks always run.
3. **Push.** `git push -u origin <branch>`.
4. **Open the PR** with `gh pr create` against `main`, or the active phase branch.
   - Title: the commit subject.
   - Body: `## Summary` (bullets on behavior and why) and `## Test plan`. Tick only the checks that actually ran in this session, with their results (`make test` (96 passed)); leave the rest unticked for the user.
   - End the body with the PR attribution line from the current system reminder.
5. **Update memory** when the branch completes or changes a pending item there.
6. **Report**: PR URL, commit hash, and any step the user runs after merging (pull, `uv sync`, one-time config). Done when the PR URL is printed.
