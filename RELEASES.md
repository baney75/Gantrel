# Releases: Nightly and Stable

Gantrel ships on two update channels. Users pick one in settings and can switch at any time.

## Channels

| Channel | Branch | Who it's for | How often |
|---|---|---|---|
| **Nightly** | `main` | Testers and people who want the newest features | Every night, when `main` has new commits and CI is green |
| **Stable** | `stable` | Everyone else | When a tested release is promoted |

## How a change reaches users

1. Work happens on feature branches and merges into `main` by pull request, with CI green.
2. Each night, `main` is built and published as a Nightly release tagged `nightly-YYYY-MM-DD`.
3. When Nightly has been solid, `main` is merged into `stable` and tagged `vMAJOR.MINOR.PATCH` as a Stable release.
4. Urgent fixes go to `stable` through a pull request, then get merged back into `main`.

## Update rules for the app

- Updates are signed and verified before they install.
- User data is backed up before every update, and migrations are reversible.
- Every update can be rolled back to the previous version.
- The app shows what changed, in plain words, before and after updating.
- No update ever deletes user data.
