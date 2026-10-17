import { test, expect, mock } from 'claude-code/testing'

const spy = (on: any) => {
  const clock = mock.clock(on)
  const seen: string[] = []
  on('command.run', { command: 'clear' }, () => {
    seen.push('clear')
    return { text: '' }
  })
  on('command.run', { command: 'lint' }, (_$: any, e: any) => {
    seen.push(`lint:${e.args}`)
    return { text: '' }
  })
  on('prompt.submit', (_$: any, e: any) => {
    seen.push(`submit:${e.text}`)
    return { text: e.text }
  })
  return { clock, seen }
}

test('/fresh <prompt> clears, then submits', async ($, on) => {
  const { clock, seen } = spy(on)
  await $.command.run({ command: 'fresh', args: '  fix the login bug ' })
  await clock.advance(10)
  expect(seen).toEqual(['clear', 'submit:fix the login bug'])
})

test('/fresh /cmd args clears, then runs the command', async ($, on) => {
  const { clock, seen } = spy(on)
  await $.command.run({ command: 'fresh', args: '/lint src/ --fix' })
  await clock.advance(10)
  expect(seen).toEqual(['clear', 'lint:src/ --fix'])
})

test('/fresh alone only clears', async ($, on) => {
  const { clock, seen } = spy(on)
  await $.command.run({ command: 'fresh' })
  await clock.advance(10)
  expect(seen).toEqual(['clear'])
})
