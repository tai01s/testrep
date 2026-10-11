import vo from "./vo.en.json";

export const FPS = 30;

export type Word = { text: string; start: number; end: number };
export type Line = { id: string; text: string; duration: number; words: Word[]; start: number; end: number; next: number };

// pause after each narration line, in seconds (the "nobody" beat gets room to breathe)
const GAP_AFTER: Record<string, number> = {
  hook: 0.5,
  setup: 0.3,
  trees: 0.3,
  sing: 0.6,
  answer: 0.4,
  morning: 0.5,
  nobody: 1.4,
  meet: 0.3,
  bury: 0.6,
  football: 0.4,
  lasts: 0.4,
  orders: 0.4,
  war: 0.7,
};
const LEAD = 2.2; // a few seconds of gunfire before the narrator speaks
export const TAIL = 3.2;

export const lines: Line[] = (() => {
  let t = LEAD;
  return (vo as Omit<Line, "start" | "end" | "next">[]).map((l) => {
    const start = t;
    t += l.duration + (GAP_AFTER[l.id] ?? 0.3);
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

/** Absolute time the first word starting with `prefix` is spoken in a line. */
export const W = (id: string, prefix: string) => {
  const w = L[id].words.find((x) => x.text.toLowerCase().startsWith(prefix.toLowerCase()));
  if (!w) throw new Error(`word "${prefix}" not in line ${id}`);
  return L[id].start + w.start;
};
