---
name: delegate-to-school-model
description: Use on any task with heavy reading or mechanical work (whole chapters or books, many files, pulling quotes, researching several candidates) to hand that work to the free school model, while you do the judging.
---

# Delegation to the school model (decide this yourself on every task)

How to reach it: run `school "<brief>"` in the shell, from the folder that holds the source files.
- It spreads runs over 3 API keys, max 4 at once per key (12 total). Extra runs wait for a free slot, so launch independent briefs in parallel:
  `school "<brief 1>" > /tmp/r1.txt & school "<brief 2>" > /tmp/r2.txt & wait`
- If `school` is not found, try `~/.local/bin/school` and `$(npm prefix -g)/bin/school` before giving up.
- If it is still missing or says no keys were found, the environment's setup script didn't run: tell me in one line and do the work yourself.

Use ONLY this model for delegation. It's fast and free but weaker at reasoning, and it may invent quotes or page numbers.
You are the lead: it gathers, you judge.

## When to delegate (no need to ask me)
Delegate when ALL of these are true:
- The work is mostly reading, extracting, summarising, listing or drafting.
- The result can be checked (quotes, page refs, facts, code that runs).
- Doing it yourself would take a lot of reading (whole chapters, many files, several candidates).

Do it yourself when:
- The task is small (writing the brief would take as long as doing it).
- It's mainly judgment: building criteria, weighing evidence, comparing, deciding.
- It needs our conversation's context that can't fit in a brief.

## How to brief
Every brief is standalone (it can't see our chat) and includes:
1. Goal: one sentence on what the result is for.
2. Input: exact files, chapters or pages to read; tell it to read them in full, not search for keywords.
   Text files with `=== PDF page N ===` markers: tell it to cite those page numbers.
3. Output format: numbered points or a table; verbatim quotes with page refs; under N words.
4. Honesty rule: "If the text doesn't support something, say so. Don't guess."

Split big jobs into chunks (one chapter or one candidate per brief) and run independent briefs in parallel.

## How to check results
- Spot-check at least 2-3 quotes and page refs against the source yourself (grep the file). If any are wrong, treat the whole result as unreliable.
- Look for what's missing: did it cover every part of the brief?
- Never take its conclusions as your own; only use its evidence.
- Write "Review:" after each result: what you checked, what held up, what you corrected or dropped.

## When it fails
- Vague or wrong: re-brief once with a sharper, narrower task, saying what was wrong.
- Fails twice: do that part yourself and mention it in the Review.
- If the school model is unavailable, do the work yourself and tell me.

## Keep me informed
Start each delegation with a one-line note: "Delegating: <what> (<n> briefs)".
In your final answer, separate what the evidence supports from your own interpretation, and say plainly when something only weakly fits.
