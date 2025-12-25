Analyse the current git diff and propose a series of logical, atomic commits.

## Context Awareness

Before analysing the diff, review the current conversation to understand:
- What problem or feature was being addressed
- Key decisions or trade-offs discussed
- The user's original intent

Use this context to write commit messages that explain the rationale behind changes, not just describe what changed. The diff remains the primary source of truth for *what* changed; the conversation provides the *why*.

## Instructions

1. Run `git diff` to get all unstaged changes and `git diff --cached` for staged changes
2. Run `git status` to see untracked files
3. Analyse the changes and group them by:
   - Feature/functionality (changes that belong together logically)
   - File type/layer (e.g., API changes, frontend changes, config changes)
   - Independence (changes that can stand alone without breaking the build)

4. For each proposed commit, provide:
   - A clear, imperative commit message (max 72 chars for subject)
   - The specific files or hunks to include (can be partial file changes)
   - Why these changes belong together
   - The git commands to stage those specific changes

5. Order the commits logically (e.g., infrastructure first, then features, then tests)

6. Present the proposal in this format:

```
## Proposed Commits

### Commit 1: <commit message>
Changes:
- path/to/file1 (entire file)
- path/to/file2 (lines 10-25: description of the hunk)

Staging commands:
git add path/to/file1
git add -p path/to/file2  # Select hunk for <description>

Rationale: <why these changes belong together>

---

### Commit 2: <commit message>
...
```

## Partial File Commits

When a file contains changes belonging to multiple commits:
1. Identify each distinct hunk using `git diff` output (look for @@ markers)
2. Specify which line ranges or hunks belong to each commit
3. Provide `git add -p <file>` commands with instructions on which hunks to accept (y) or skip (n)
4. For complex cases, show the exact diff context to help identify the right hunk

Example for partial staging:
```
git add -p path/to/file.py
# Hunk 1 (@@ -10,5 +10,8 @@): Accept (y) - adds new import
# Hunk 2 (@@ -45,10 +48,15 @@): Skip (n) - belongs to commit 2
```

## Guidelines

- Each commit should be atomic and not break the build
- Prefer smaller, focused commits over large mixed ones
- Separate refactoring from feature changes
- Separate config/infrastructure changes from code changes
- When a file has mixed changes, use partial staging to split them
- If changes are too intermingled to separate cleanly, note this and suggest the best compromise
