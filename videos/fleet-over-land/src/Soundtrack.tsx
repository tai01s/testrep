import React from "react";
import { Html5Audio, Sequence, interpolate, staticFile } from "remotion";
import { FPS, Timeline, useTimeline } from "./timeline";

// "Тусовщица" (ftshsm). The track's first drop lands at 30.95 s and the second,
// after a quiet break, at 107.75 s. Drop 1 hits as the ships are dragged; drop 2
// hits on "Constantinople falls".
const MUSIC = staticFile("music/tusovshchitsa.m4a");
const DROP_1 = 30.95;
const DROP_2 = 107.75;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Duck the music under the narration. */
const duck = (t: number, lines: Timeline["lines"]) => {
  let d = 99;
  for (const l of lines) {
    if (t >= l.start - 0.1 && t <= l.end) return 0;
    d = Math.min(d, Math.abs(t - (l.start - 0.1)), Math.abs(t - l.end));
  }
  return Math.min(1, d / 0.35);
};

const musicLevel = (t: number, { lines, L, TOTAL }: Timeline) => {
  const under = 0.16, open = 0.42;
  const fadeOut = interpolate(t, [TOTAL - 1.2, TOTAL], [1, 0], clamp);
  // the end card lets the track breathe
  const tail = t > L.outro.end ? 0.55 : open;
  return (under + (tail - under) * duck(t, lines)) * fadeOut;
};

const sfx = (name: string, at: number, volume = 1) => ({ name, at, volume });

export const Soundtrack: React.FC = () => {
  const tl = useTimeline();
  const { L, S, W, lang, lines } = tl;
  // segment A: from the start of the track, aligned so drop 1 meets "Then they drag"
  const dragAt = L.drag.start;
  const aFrom = Math.max(0, dragAt - DROP_1); // video time where segment A starts
  const aTrim = Math.max(0, DROP_1 - dragAt); // track time at that moment
  // segment B: crossfade into the break before drop 2, aligned to "falls"
  const fallsAt = W("fall", "falls");
  const bFrom = S("fall") - 0.6;
  const bTrim = DROP_2 - (fallsAt - bFrom);
  const xfade = 0.8;

  const effects = [
    sfx("boom", 0.05, 0.9),
    sfx("clank", W("hook1", "chain") - 0.05, 0.6),
    sfx("whoosh", S("hook2") - 0.1, 0.6),
    sfx("whoosh", S("setup") - 0.15, 0.5),
    sfx("clank", W("chain", "chain") - 0.05, 0.55),
    sfx("thud", W("fail", "fails") + 0.05, 0.9),
    sfx("whoosh", S("twist") - 0.1, 0.5),
    sfx("drag", S("drag") + 0.1, 0.55),
    sfx("whoosh", S("oars") - 0.15, 0.45),
    sfx("drag", S("oars"), 0.35),
    sfx("splash", S("reveal") - 0.1, 0.6),
    sfx("boom", fallsAt - 0.05, 1),
    sfx("whoosh", S("outro") - 0.15, 0.5),
  ];

  return (
    <>
      <Sequence from={Math.round(aFrom * FPS)} durationInFrames={Math.round((bFrom + xfade - aFrom) * FPS)}>
        <Html5Audio
          src={MUSIC}
          trimBefore={Math.round(aTrim * FPS)}
          volume={(f) => {
            const t = aFrom + f / FPS;
            const fadeIn = interpolate(t, [aFrom, aFrom + 1.5], [0.3, 1], clamp);
            const out = interpolate(t, [bFrom, bFrom + xfade], [1, 0], clamp);
            return musicLevel(t, tl) * fadeIn * out;
          }}
        />
      </Sequence>
      <Sequence from={Math.round(bFrom * FPS)}>
        <Html5Audio
          src={MUSIC}
          trimBefore={Math.round(bTrim * FPS)}
          volume={(f) => {
            const t = bFrom + f / FPS;
            return musicLevel(t, tl) * interpolate(t, [bFrom, bFrom + xfade], [0, 1], clamp);
          }}
        />
      </Sequence>
      {lines.map((l) => (
        <Sequence key={l.id} from={Math.round(l.start * FPS)}>
          <Html5Audio src={staticFile(`vo/${lang}/${l.id}.wav`)} volume={1} />
        </Sequence>
      ))}
      {effects.map((e, i) => (
        <Sequence key={i} from={Math.max(0, Math.round(e.at * FPS))}>
          <Html5Audio src={staticFile(`sfx/${e.name}.wav`)} volume={e.volume} />
        </Sequence>
      ))}
    </>
  );
};
