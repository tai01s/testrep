import vo from "./vo.json";

export const FPS = 30;

export type Word = { text: string; start: number; end: number };
export type Line = { id: string; text: string; duration: number; words: Word[]; start: number; end: number; next: number };

// pause after each narration line, in seconds
const GAP_AFTER: Record<string, number> = {
  hook1: 0.1,
  hook2: 0.45,
  setup: 0.2,
  chain: 0.15,
  fail: 0.35,
  twist: 0.3,
  road: 0.15,
  drag: 0.2,
  oars: 0.3,
  reveal: 0.25,
  stretch: 0.45,
  fall: 0.4,
};
const LEAD = 0.4;
export const TAIL = 2.8;

export const lines: Line[] = (() => {
  let t = LEAD;
  return (vo as Omit<Line, "start" | "end" | "next">[]).map((l) => {
    const start = t;
    t += l.duration + (GAP_AFTER[l.id] ?? 0.25);
    return { ...l, start, end: start + l.duration, next: t };
  });
})();

export const L: Record<string, Line> = Object.fromEntries(lines.map((l) => [l.id, l]));
export const TOTAL = lines[lines.length - 1].end + TAIL;

/** Scene boundaries: a scene runs from its line's start to the next line's start. */
export const S = (id: string) => (lines[0].id === id ? 0 : L[id].start);
export const E = (id: string) => {
  const i = lines.findIndex((l) => l.id === id);
  return i === lines.length - 1 ? TOTAL : lines[i + 1].start;
};

/** Absolute time a word (first match of a prefix, case-insensitive) is spoken in a line. */
export const W = (id: string, prefix: string) => {
  const line = L[id];
  const w = line.words.find((x) => x.text.toLowerCase().startsWith(prefix.toLowerCase()));
  if (!w) throw new Error(`word "${prefix}" not in line ${id}`);
  return line.start + w.start;
};

/** The line being spoken (or most recently spoken) at time t. */
export const lineAt = (t: number) => {
  let cur = lines[0];
  for (const l of lines) if (t >= S(l.id)) cur = l;
  return cur;
};
