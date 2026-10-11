import { Easing, interpolate } from "remotion";
import { Timeline } from "./timeline";

export type Cam = { cx: number; cy: number; w: number };
type Key = { t: number } & Cam;

const k = (t: number, cx: number, cy: number, w: number): Key => ({ t, cx, cy, w });

// Camera path over the map. Two keys at nearly the same time make a cut.
const keys = ({ S, E }: Timeline): Key[] => [
  k(0, 712, 600, 300),
  k(E("hook1"), 700, 594, 240),
  // hook2 is a full-screen side view; cut the map to the wide shot under it
  k(S("setup"), 470, 610, 1300),
  k(E("setup"), 455, 600, 1020),
  k(S("chain") + 1.0, 640, 585, 520),
  k(E("chain"), 662, 588, 420),
  k(S("fail") + 0.5, 726, 592, 330),
  k(E("fail"), 722, 592, 310),
  k(S("twist") + 0.9, 655, 460, 640),
  k(E("twist"), 650, 450, 580),
  k(S("road") + 0.6, 652, 420, 500),
  k(E("road"), 650, 418, 450),
  k(S("drag") + 0.3, 735, 405, 400),
  k(S("drag") + 3.4, 585, 400, 440),
  k(E("drag"), 520, 450, 480),
  // oars is a side view
  k(S("reveal"), 540, 500, 560),
  k(E("reveal"), 535, 505, 480),
  k(S("stretch") + 0.9, 430, 620, 920),
  k(E("stretch"), 430, 620, 860),
  k(S("fall") + 0.8, 450, 640, 1080),
  k(E("fall"), 450, 640, 820),
  k(E("fall") + 2, 450, 640, 760),
];

const cache = new Map<Timeline, Key[]>();

export const cameraAt = (t: number, tl: Timeline): Cam => {
  if (!cache.has(tl)) cache.set(tl, keys(tl));
  const ks = cache.get(tl)!;
  if (t <= ks[0].t) return ks[0];
  for (let i = 1; i < ks.length; i++) {
    const a = ks[i - 1], b = ks[i];
    if (t <= b.t) {
      const u = interpolate(t, [a.t, b.t], [0, 1], { easing: Easing.inOut(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      // zoom moves in log space so it feels even
      return { cx: a.cx + (b.cx - a.cx) * u, cy: a.cy + (b.cy - a.cy) * u, w: Math.exp(Math.log(a.w) + (Math.log(b.w) - Math.log(a.w)) * u) };
    }
  }
  return ks[ks.length - 1];
};
