import { createContext, useContext } from "react";
import en from "./vo.en.json";
import tr from "./vo.tr.json";
import { Lang, STRINGS } from "./i18n";

export const FPS = 30;

export type Word = { text: string; start: number; end: number };
export type Line = { id: string; text: string; duration: number; words: Word[]; start: number; end: number; next: number };
type VoLine = Omit<Line, "start" | "end" | "next">;

const VO: Record<Lang, VoLine[]> = { en, tr };

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

const makeTimeline = (lang: Lang) => {
  let t = LEAD;
  const lines: Line[] = VO[lang].map((l) => {
    const start = t;
    t += l.duration + (GAP_AFTER[l.id] ?? 0.25);
    return { ...l, start, end: start + l.duration, next: t };
  });
  const L: Record<string, Line> = Object.fromEntries(lines.map((l) => [l.id, l]));
  const TOTAL = lines[lines.length - 1].end + TAIL;

  /** Scene boundaries: a scene runs from its line's start to the next line's start. */
  const S = (id: string) => (lines[0].id === id ? 0 : L[id].start);
  const E = (id: string) => {
    const i = lines.findIndex((l) => l.id === id);
    return i === lines.length - 1 ? TOTAL : lines[i + 1].start;
  };

  /**
   * Absolute time a word is spoken. Cues are written against the English script
   * (first word starting with `prefix`); other languages map them in i18n.ts.
   */
  const W = (id: string, prefix: string) => {
    const p = (STRINGS[lang].cues[`${id}.${prefix}`] ?? prefix).toLocaleLowerCase(lang);
    const w = L[id].words.find((x) => x.text.toLocaleLowerCase(lang).startsWith(p));
    if (!w) throw new Error(`word "${p}" not in ${lang} line ${id}`);
    return L[id].start + w.start;
  };

  return { lang, lines, L, TOTAL, S, E, W, str: STRINGS[lang] };
};

export type Timeline = ReturnType<typeof makeTimeline>;

const cache = new Map<Lang, Timeline>();
export const timelineFor = (lang: Lang) => {
  if (!cache.has(lang)) cache.set(lang, makeTimeline(lang));
  return cache.get(lang)!;
};

export const TimelineContext = createContext<Timeline>(timelineFor("en"));
export const useTimeline = () => useContext(TimelineContext);
