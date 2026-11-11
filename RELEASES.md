# Releases: Stable and Dev

Gantrel must be stable, so it ships on two update channels only. There is no nightly channel.

## Channels

| Channel | Branch | Who it's for | How often |
|---|---|---|---|
| **Stable** | `stable` | Everyone. This is the default and the only channel most people see. | When a tested release is promoted |
| **Dev** | `main` | Developers and testers only. Hidden behind a developer setting and never used for real work. | When `main` has new commits and CI is green |

## How a change reaches users

1. Work happens on feature branches and merges into `main` by pull request, with CI green.
2. `main` is published to the Dev channel, tagged `dev-YYYY-MM-DD`.
3. A Dev build is promoted to Stable only after every test in TESTING.md passes for every supported model, with no regressions. It is then merged into `stable` and tagged `vMAJOR.MINOR.PATCH`.
4. Urgent fixes go to `stable` through a pull request, then get merged back into `main`.

## Update rules for the app

- Updates are signed and verified before they install.
- User data is backed up before every update, and migrations are reversible.
- Every update can be rolled back to the previous version.
- The app shows what changed, in plain words, before and after updating.
- No update ever deletes user data or changes work in progress without asking.
