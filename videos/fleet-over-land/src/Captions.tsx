import React from "react";
import { Easing, interpolate } from "remotion";
import { lines, Word } from "./timeline";
import { fonts } from "./fonts";

type Chunk = { words: (Word & { abs: number })[]; start: number; end: number };

// TikTok-style captions: 1-3 words at a time, the spoken word highlighted
const chunks: Chunk[] = (() => {
  const out: Chunk[] = [];
  for (const line of lines) {
    let cur: Chunk["words"] = [];
    const flush = () => {
      if (cur.length) out.push({ words: cur, start: cur[0].abs, end: line.start + line.words[line.words.length - 1].end });
      cur = [];
    };
    line.words.forEach((w) => {
      cur.push({ ...w, abs: line.start + w.start });
      const long = cur.reduce((n, x) => n + x.text.length, 0) > 14;
      if (/[.,?!]$/.test(w.text) || cur.length === 3 || long) flush();
    });
    flush();
  }
  // each chunk stays up until the next one starts (or a short beat after its line)
  out.forEach((c, i) => {
    const next = out[i + 1];
    c.end = next && next.start - c.end < 0.6 ? next.start : c.end + 0.35;
  });
  return out;
})();

const OUTLINE = (() => {
  const r = 7;
  const s: string[] = [];
  for (let a = 0; a < 16; a++) s.push(`${(Math.cos((a / 16) * Math.PI * 2) * r).toFixed(1)}px ${(Math.sin((a / 16) * Math.PI * 2) * r).toFixed(1)}px 0 #0b0b0b`);
  s.push("0 10px 18px rgba(0,0,0,0.55)");
  return s.join(",");
})();

export const Captions: React.FC<{ t: number }> = ({ t }) => {
  const chunk = chunks.find((c) => t >= c.start && t < c.end);
  if (!chunk) return null;
  const inT = t - chunk.start;
  const pop = interpolate(inT, [0, 0.12], [0.86, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.back(2.5)) });
  return (
    <div
      style={{
        position: "absolute", left: 70, right: 130, top: 1300, display: "flex", flexWrap: "wrap", justifyContent: "center",
        transform: `scale(${pop})`,
      }}
    >
      {chunk.words.map((w, i) => {
        const active = t >= w.abs && (i === chunk.words.length - 1 || t < chunk.words[i + 1].abs);
        const said = t >= w.abs;
        return (
          <span
            key={i}
            style={{
              fontFamily: fonts.caption, fontWeight: 900, fontSize: 86, lineHeight: 1.12, textTransform: "uppercase",
              color: active ? "#FFD23F" : "#ffffff", opacity: said ? 1 : 0.92, textShadow: OUTLINE,
              transform: `scale(${active ? 1.08 : 1})`, display: "inline-block", margin: "0 13px",
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
