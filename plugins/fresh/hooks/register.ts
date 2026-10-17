import type { Register } from 'claude-code'

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'fresh',
      description: 'Clear the conversation, then submit a prompt or /command',
      argumentHint: '<prompt | /command args>',
    })
    return next(e)
  })

  on('command.run', { command: 'fresh' }, ($, e) => {
    const text = (e.args ?? '').trim()

    // The engine refuses $.command.run from inside a command.run hook (it
    // would wait on this very turn), so the work runs from a timer instead.
    $.clock.after(0, async () => {
      await $.command.run({ command: 'clear' })
      if (!text) return

      // "/name args" runs as a command (or skill) after the clear; an unknown
      // name rejects, and the text goes to the model as a plain prompt instead.
      const slash = /^\/(\S+)\s*([\s\S]*)$/.exec(text)
      if (slash) {
        try {
          await $.command.run({ command: slash[1], args: slash[2] })
          return
        } catch {}
      }
      await $.prompt.submit({ text, asUser: true })
    })

    return { text: text ? 'Clearing, then running your input.' : 'Clearing.' }
  })
}
