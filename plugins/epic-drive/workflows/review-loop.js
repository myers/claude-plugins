export const meta = {
  name: 'review-loop',
  description: 'Per lane item: code (optional), plan-coverage check, fresh review, then fix and re-review until APPROVE (max rounds configurable)',
  whenToUse: 'Epic drive with parallel lanes: take finished or to-be-coded lane branches through review without waking the controller per bounce. args = {drive: {...}, items: [...]} or a bare items array. drive: preamble (text opening every prompt: who dispatched, authorization, tracker root), coderBrief (path to the filled coder-brief.md), epic (where follow-ups are filed), reviewSkills (list), reviewRead (what reviewers read besides issues and diffs), reviewChecks (extra checklist lines), gates (list of gate commands; {cpus} is replaced by the item slice), ci (how to push and gate on CI; omit for local-only), cpus (default slice), maxRounds (default 3), reviewModel (default opus). items[]: key, branch, worktree, base, code (slice text; omit to start at review), commits, issues, plan, plan_items (list for the coverage check), focus, startFix ({head, blocking} to start at a fix), cpus, drive (per-item overrides). See the epic-drive README.',
  phases: [{ title: 'Review' }, { title: 'Fix' }],
}

const RAW = Array.isArray(args) ? { items: args } : (args || {})
const DRIVE = RAW.drive || {}

const VERDICT = { type: 'object', properties: {
  verdict: { type: 'string', enum: ['APPROVE', 'REJECT'] },
  blocking: { type: 'array', items: { type: 'string' } },
  head: { type: 'string', description: 'branch head sha reviewed' },
  summary: { type: 'string' } }, required: ['verdict', 'blocking', 'head', 'summary'] }
const FIXED = { type: 'object', properties: {
  head: { type: 'string' }, fixed: { type: 'array', items: { type: 'string' } },
  notfixed: { type: 'array', items: { type: 'string' } }, gates: { type: 'string' } },
  required: ['head', 'fixed', 'notfixed', 'gates'] }
const COVER = { type: 'object', properties: {
  complete: { type: 'boolean' }, missing: { type: 'array', items: { type: 'string' } } },
  required: ['complete', 'missing'] }

const cfg = (it) => Object.assign({}, DRIVE, it.drive || {})
const cpus = (it) => it.cpus || cfg(it).cpus || ''
const pre = (it) => (cfg(it).preamble ? cfg(it).preamble + '\n' : '')
const list = (xs) => xs.map((x, i) => (i + 1) + '. ' + x).join(' ')
const gateLines = (it) => (cfg(it).gates || []).map((g) => '- ' + g.split('{cpus}').join(cpus(it) || '<your slice>')).join('\n')
const briefLine = (it) => {
  const d = cfg(it)
  const slice = cpus(it) ? ` Run every taskset as "taskset -c ${cpus(it)}" (this lane's CPU slice).` : ''
  return (d.coderBrief ? `First read ${d.coderBrief} and follow it exactly, except as this prompt says.` : '') + slice
}
const planLine = (it) => (it.plan ? ' Plan: ' + it.plan + '.' : '')

// Plan-coverage gate: a slice that shipped only part of its plan goes back to the coder, not to review.
const cover = (it, head, n) => agent(`${pre(it)}Plan-coverage check. Edit no code, run no tests, post no comments. Branch ${it.branch} in ${it.worktree}, head ${head}, base ${it.base}.${planLine(it)}
The slice as dispatched: ${it.code}
${it.plan_items && it.plan_items.length
    ? 'The slice requires exactly these items: ' + list(it.plan_items)
    : 'List every item this slice requires: each function or struct to port, each named test, each named deletion, each named commit split.'}
For each item, look in \`git diff ${it.base}..${head}\` (the diff, not the commit messages) for it. Return complete=true only if every item is present. Otherwise list each missing item by its plan name and source symbol.`,
  { label: `cover:${it.key}:${n}`, phase: 'Fix', schema: COVER, effort: 'low' })

const review = (it, round, prior) => {
  const d = cfg(it)
  const skills = (d.reviewSkills || []).join(' and ')
  return agent(`${pre(it)}Fresh-context review, round ${round}, of branch ${it.branch} in the worktree ${it.worktree}. Commits: ${it.commits}. Issues: ${it.issues}.${planLine(it)}
${skills ? 'Load the ' + skills + ' skills. ' : ''}Read each issue with its comments${d.epic ? ', the epic ' + d.epic : ''}${d.reviewRead ? ', ' + d.reviewRead : ''}, and the diffs. Re-derive every cited source independently; do not trust the commits' citations.
Check each of these:
- plan coverage first: every function, record type, test and deletion the plan names for this slice is in the diff; a missing one is blocking finding 1, named by its source symbol${it.plan_items && it.plan_items.length ? ' (the plan items: ' + list(it.plan_items) + ')' : ''}
- vacuous acceptance criteria
- one mutation counterfactual per ticket or slice: revert the key line, show red, restore it
- stale comments
${(d.reviewChecks || []).map((c) => '- ' + c).join('\n')}
${gateLines(it) ? 'Also run these gates on the branch tip, waiting in the foreground for each:\n' + gateLines(it) : ''}
${d.ci ? 'CI: ' + d.ci : ''}
${it.focus ? 'Also judge specifically: ' + it.focus : ''}${prior ? '\nPrior round blocking findings, now claimed fixed (range-diff against the previously reviewed head ' + prior.head + '): ' + prior.blocking.join(' | ') : ''}
Post one APPROVE/REJECT verdict comment, with numbered findings, on each issue${d.ci ? ', including the CI run id' : ''}. ${d.epic ? 'File non-blocking gaps under ' + d.epic + ' after deduping. ' : ''}Edit no code, open no PRs, close no issues${d.ci ? '; the branch push for CI is the only push you make' : ', and push nothing'}. Leave the worktree clean at its head.`,
    { label: `review:${it.key}:r${round}`, phase: 'Review', model: d.reviewModel || 'opus', schema: VERDICT })
}

const fix = (it, v) => {
  const d = cfg(it)
  return agent(`${pre(it)}${briefLine(it)}
You are fixing an existing branch, not creating one. The branch is ${it.branch}, in the existing worktree ${it.worktree}; the issues are ${it.issues}.
A fresh review REJECTed head ${v.head} with these blocking findings: ${list(v.blocking)}
Read the verdict comments on the issues for the details. Fix every finding, and fold each fix into its owning commit with fixup plus autosquash. Then rerun the reviewer checklist and gates${d.coderBrief ? ' from the common brief' : ''}, waiting in the foreground for each.
${gateLines(it)}
Comment the new SHAs on each issue.${d.ci ? ' Push the fixed head so CI starts on it before the re-review. CI: ' + d.ci : ''}
Work the findings in order; finding 1 first. Every finding ends up under fixed or under notfixed with its reason; account for every one. A finding that names missing slice work (a function, record type, test or deletion that does not exist yet) is fixed only by writing that work.
Return the new head and which findings you fixed. If a finding conflicts with the reference source, put it under notfixed and give its file:line.`,
    { label: `fix:${it.key}`, phase: 'Fix', schema: FIXED })
}

const result = (it, verdict, head, rounds, blocking, summary) => ({ key: it.key, branch: it.branch, verdict, head, rounds, blocking, summary })

const results = await pipeline(RAW.items || [], async (it) => {
  const maxRounds = cfg(it).maxRounds || 3
  if (it.code) {
    const c = await agent(`${pre(it)}${briefLine(it)}
${it.code}
Worktree: ${it.worktree}, branch ${it.branch}, created from ${it.base}.
Return the branch head sha and the commit list.`, { label: `code:${it.key}`, phase: 'Fix', schema: FIXED })
    if (!c) return result(it, 'ERROR', null, 0, ['coder returned nothing'], '')
    let head = c.head
    for (let n = 1; n <= 2; n++) {
      const cv = await cover(it, head, n)
      if (!cv || cv.complete) break
      log(`${it.key}: coverage ${n} missing ${cv.missing.length}: ${cv.missing.join('; ')}`)
      if (n === 2) return result(it, 'INCOMPLETE', head, 0, cv.missing, 'coder twice returned a partial slice')
      const c2 = await agent(`${pre(it)}${briefLine(it)}
You are continuing an existing branch, not creating one: ${it.branch} in ${it.worktree}, head ${head}. The slice as dispatched: ${it.code}
A plan-coverage check found these slice items missing from the diff: ${list(cv.missing)}
Write each missing item, tests first, and commit after each. The slice is not done until all are in the diff. Return the new head and the items you added.`,
        { label: `code:${it.key}:cont${n}`, phase: 'Fix', schema: FIXED })
      if (!c2) break
      head = c2.head
    }
    it.commits = it.commits || ('branch ' + it.branch + ' head ' + head + '; ' + c.fixed.join('; '))
  }
  let v = it.startFix ? { verdict: 'REJECT', head: it.startFix.head, blocking: it.startFix.blocking } : await review(it, 1, null)
  let round = 1
  while (v && v.verdict === 'REJECT' && round < maxRounds) {
    const f = await fix(it, v)
    if (!f) break
    if (f.head === v.head) { log(`${it.key}: fix round changed nothing (notfixed: ${f.notfixed.join('; ')})`); break }
    round++
    v = await review(it, round, v)
  }
  return v ? result(it, v.verdict, v.head, round, v.blocking, v.summary || '') : result(it, 'ERROR', null, round, [], '')
})
return results
