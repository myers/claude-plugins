# fresh

A Claude Code mod that adds `/fresh`: clear the conversation, then submit what follows as the next prompt, in the same session.

## Install

```
/plugin install fresh --marketplace myers/claude-plugins
```

## Usage

| Input | Result |
|-------|--------|
| `/fresh fix the login bug` | clears, then submits the text as a user prompt |
| `/fresh /skill-name args` | clears, then runs `/skill-name args`; if the name is unknown, submits the text as a plain prompt |
| `/fresh` | clears only |

The clear and submit run from a zero-delay timer, because the engine refuses `$.command.run` inside a `command.run` hook.

Unverified live: `/fresh /skill-name` and bare `/fresh`. Plain-prompt path verified.

## Develop

`claude --plugin-dir plugins/fresh`. The engine writes `.claude-plugin/types/` (gitignored); then `tsc -p plugins/fresh`.
