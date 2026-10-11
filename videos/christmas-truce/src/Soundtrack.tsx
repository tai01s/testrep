import React from "react";
import { Html5Audio, Sequence, interpolate, staticFile } from "remotion";
import { E, FPS, L, S, TOTAL, W, lines } from "./timeline";

// "lilacs (slowed)" by velours & azrxel
const MUSIC = staticFile("music/lilacs.m4a");
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0 while the narrator speaks, rising to 1 in the gaps. */
const openness = (t: number) => {
  let d = 99;
  for (const l of lines) {
    if (t >= l.start - 0.1 && t <= l.end) return 0;
    d = Math.min(d, Math.abs(t - (l.start - 0.1)), Math.abs(t - l.end));
  }
  return Math.min(1, d / 0.4);
};

const musicLevel = (t: number) => {
  // music arrives as the guns stop, and drops out for "Nobody shoots."
  const arrive = interpolate(t, [W("hook", "silent") - 0.3, W("hook", "silent") + 2.5], [0, 1], clamp);
  const hush = 1 - interpolate(t, [S("nobody") - 0.6, S("nobody")], [0, 0.85], clamp) * interpolate(t, [E("nobody") - 0.2, E("nobody") + 1.2], [1, 0], clamp);
  const fadeOut = interpolate(t, [TOTAL - 1.5, TOTAL], [1, 0], clamp);
  const tail = t > L.outro.end ? 0.5 : 0.34;
  return (0.12 + (tail - 0.12) * openness(t)) * arrive * hush * fadeOut;
};

const sfx = (name: string, at: number, volume = 1) => ({ name, at, volume });

export const Soundtrack: React.FC = () => {
  const kicks = Array.from({ length: 6 }, (_, i) => sfx("kick", S("football") + i * 0.75, 0.5));
  const effects = [
    sfx("barrage", 0, 0.9),
    sfx("rifles", 0.4, 0.7),
    sfx("flare", 0.2, 0.4),
    sfx("rifles", 1.9, 0.6),
    sfx("barrage", 3.2, 0.6),
    sfx("rifles", 4.6, 0.4),
    sfx("whoosh", W("setup", "Between") - 0.2, 0.4),
    sfx("bell", S("morning") - 0.2, 0.5),
    sfx("bell", S("morning") + 1.6, 0.3),
    ...kicks,
    sfx("flip", W("lasts", "Boxing") - 0.15, 0.6),
    sfx("flip", W("lasts", "new") - 0.15, 0.6),
    sfx("thud", W("orders", "never") - 0.05, 0.9),
    sfx("boom", S("war") - 0.1, 0.9),
    sfx("barrage", S("war") + 0.4, 0.6),
    sfx("rifles", S("war") + 1.5, 0.5),
    sfx("barrage", S("war") + 3.2, 0.4),
  ];
  return (
    <>
      <Html5Audio src={MUSIC} volume={(f) => musicLevel(f / FPS)} />
      {/* cold wind under everything, looped */}
      {Array.from({ length: Math.ceil(TOTAL / 11) }, (_, i) => (
        <Sequence key={`w${i}`} from={Math.round(i * 11 * FPS)} durationInFrames={Math.round(12 * FPS)}>
          <Html5Audio src={staticFile("sfx/wind.wav")} volume={0.22} />
        </Sequence>
      ))}
      {lines.map((l) => (
        <Sequence key={l.id} from={Math.round(l.start * FPS)}>
          <Html5Audio src={staticFile(`vo/en/${l.id}.wav`)} />
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
