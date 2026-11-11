# Skills

Skills are the instructions that make the models in Gantrel do their work right. They must be standardized and powerfully good: a weak or vague skill is a bug.

## The standard

Every skill is a folder in `skills/` with a `SKILL.md` file. Copy `skills/_template/` to start a new one.

Each `SKILL.md` has:

1. **Frontmatter:** `name` (kebab-case, same as the folder) and `description` (one line saying exactly when to use it).
2. **Goal:** what a finished, correct result looks like.
3. **Inputs:** what the skill needs before it starts.
4. **Steps:** the exact procedure, in order.
5. **Rules and checks:** hard constraints and how to verify the output before returning it.
6. **Sources:** references the skill relies on, with links.

Keep a skill focused on one job. Put long reference material in files next to `SKILL.md` and link to them.
