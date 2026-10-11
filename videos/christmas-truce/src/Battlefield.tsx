import React, { useMemo } from "react";
import { Easing, interpolate, interpolateColors, random } from "remotion";
import { CandleTree, Football, Item, Note, Pose, Soldier } from "./figures";
import { E, S, W } from "./timeline";

// World: a side-on panorama 3200 wide. Ground surface at y=1150.
// British trench on the left, German trench on the right, no man's land between.
export const GROUND = 1150;
const GB_TRENCH = [640, 900] as const;
const DE_TRENCH = [2300, 2560] as const;
const STEP_Y = GROUND + 175; // fire-step: a soldier standing here just peeks over

export type Cam = { cx: number; cy: number; z: number };

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ramp = (t: number, a: number, b: number, easing = Easing.bezier(0.33, 0, 0.2, 1)) => interpolate(t, [a, b], [0, 1], { ...clamp, easing });
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;

const groundPath = () => {
  // surface with trench cut-outs and a few shell craters
  const pts: string[] = [`M-800,${GROUND}`];
  const trench = (a: number, b: number) => pts.push(`L${a},${GROUND} L${a + 20},${GROUND + 260} L${b - 20},${GROUND + 260} L${b},${GROUND}`);
  trench(GB_TRENCH[0], GB_TRENCH[1]);
  for (const [cx, r] of [[1370, 60], [1850, 70]]) pts.push(`L${cx - r},${GROUND} Q${cx},${GROUND + r * 0.9} ${cx + r},${GROUND}`);
  trench(DE_TRENCH[0], DE_TRENCH[1]);
  pts.push(`L4000,${GROUND} L4000,3000 L-800,3000Z`);
  return pts.join(" ");
};

const Sandbags: React.FC<{ x0: number; x1: number; rows: number }> = ({ x0, x1, rows }) => {
  const bags: React.ReactNode[] = [];
  for (let r = 0; r < rows; r++) {
    const w = 46, h = 22;
    const n = Math.floor((x1 - x0 - r * 30) / w);
    for (let i = 0; i < n; i++) {
      const x = x0 + r * 15 + i * w + (r % 2) * 20;
      bags.push(<rect key={`${r}-${i}`} x={x} y={GROUND - (r + 1) * h + 2} width={w - 2} height={h} rx={9} fill={r % 2 ? "#8c7a58" : "#7d6c4c"} stroke="#4a3e2a" strokeWidth={2} />);
    }
  }
  return <g>{bags}</g>;
};

const Wire: React.FC<{ x0: number; x1: number }> = ({ x0, x1 }) => {
  const posts: React.ReactNode[] = [];
  let d = `M${x0},${GROUND - 40}`;
  for (let x = x0; x <= x1; x += 70) {
    posts.push(<line key={x} x1={x} y1={GROUND + 6} x2={x + 6} y2={GROUND - 70} stroke="#3b2c1c" strokeWidth={6} />);
    d += ` Q${x + 35},${GROUND - 80} ${x + 70},${GROUND - 40} M${x},${GROUND - 15} Q${x + 35},${GROUND - 45} ${x + 70},${GROUND - 15} M${x + 70},${GROUND - 40}`;
  }
  return (
    <g>
      {posts}
      <path d={d} stroke="#2a2420" strokeWidth={2.5} fill="none" />
      {Array.from({ length: Math.floor((x1 - x0) / 12) }, (_, i) => (
        <path key={i} d={`M${x0 + i * 12},${GROUND - 40 - (i % 3) * 12} l4,-5 m-4,5 l-4,-5`} stroke="#2a2420" strokeWidth={2} />
      ))}
    </g>
  );
};

/** Camera path through the panorama, keyed to the narration. */
export const cameraAt = (t: number): Cam => {
  // the ground line sits at screen y=1100 so sky (titles) is above and earth (captions) below
  const k = (tt: number, cx: number, _cy: number, z: number) => ({ t: tt, cx, cy: GROUND - 140 / z, z });
  const keys = [
    k(0, 1600, 0, 0.56),
    k(E("hook"), 1600, 0, 0.6),
    k(W("setup", "Between") - 0.01, 1600, 0, 0.54),
    k(E("setup"), 1600, 0, 0.58),
    k(S("trees") + 1.2, 2200, 0, 1.05),
    k(E("trees"), 2230, 0, 1.15),
    k(E("sing"), 2260, 0, 1.3),
    k(S("answer") + 1.0, 820, 0, 1.15),
    k(W("answer", "Song") + 0.4, 1600, 0, 0.56),
    k(E("answer"), 1600, 0, 0.58),
    k(S("morning") + 1.0, 1600, 0, 0.68),
    k(E("morning"), 1600, 0, 0.7),
    k(E("nobody"), 1600, 0, 0.85),
    k(S("meet") + 1.2, 1600, 0, 1.45),
    k(E("meet"), 1600, 0, 1.6),
    k(S("bury") + 0.6, 1600, 0, 1.45),
    k(E("bury"), 1600, 0, 1.55),
    k(S("football") + 0.5, 1600, 0, 1.3),
    k(E("football"), 1600, 0, 1.38),
    k(S("lasts") + 0.6, 1600, 0, 0.8),
    k(E("orders"), 1600, 0, 0.7),
    k(E("war"), 1600, 0, 0.56),
    k(S("outro") + 0.01, 2240, 0, 1.8),
    k(E("outro"), 2240, 0, 2.0),
  ];
  if (t <= keys[0].t) return keys[0];
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i];
    if (t <= b.t) {
      const u = interpolate(t, [a.t, b.t], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
      return { cx: lerp(a.cx, b.cx, u), cy: lerp(a.cy, b.cy, u), z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), u)) };
    }
  }
  return keys[keys.length - 1];
};

export const Battlefield: React.FC<{ t: number; cam: Cam }> = ({ t, cam }) => {
  const ground = useMemo(groundPath, []);

  // --- lighting: night -> dawn -> grey day -> night of war -> night of the epilogue ---
  const dawn = ramp(t, S("morning") - 0.6, S("morning") + 2.4);
  const warNight = ramp(t, S("orders") + 1.5, S("war") + 0.8);
  const mourn = ramp(t, S("bury") - 0.2, S("bury") + 0.8) * (1 - ramp(t, S("football") - 0.2, S("football") + 0.6));
  const day = dawn * (1 - warNight);
  const skyTop = interpolateColors(day, [0, 0.4, 1], ["#070b1c", "#3b3e66", "#9fb1c6"]);
  const skyBot = interpolateColors(day, [0, 0.4, 1], ["#1b2440", "#e8a37a", "#dfe3e6"]);
  const groundCol = interpolateColors(day, [0, 1], ["#2a2a33", "#5f5a50"]);
  const snowCol = interpolateColors(day, [0, 1], ["#9aa6bf", "#f2f4f6"]);

  // --- gunfire in the hook, and again when the war resumes ---
  const firing = (t < W("hook", "silent") + 0.2 ? 1 : 0) + (t > S("war") - 0.3 && t < E("war") + 0.4 ? 1 : 0);
  const flashes: React.ReactNode[] = [];
  if (firing) {
    for (let i = 0; i < 16; i++) {
      const period = 0.9 + random(`fp${i}`) * 1.3;
      const phase = (t + random(`fo${i}`) * 3) % period;
      if (phase > 0.09) continue;
      const gb = i % 2 === 0;
      const x = gb ? GB_TRENCH[1] + 30 + random(`fx${i}`) * 40 : DE_TRENCH[0] - 30 - random(`fx${i}`) * 40;
      const y = GROUND - 30 - random(`fy${i}`) * 20;
      flashes.push(
        <g key={i}>
          <circle cx={x} cy={y} r={70} fill="url(#flashGlow)" />
          <path d={`M${x},${y} l${gb ? 46 : -46},-6 l${gb ? -40 : 40},14Z`} fill="#fff1b0" />
        </g>
      );
    }
    // shell bursts in no man's land
    for (let i = 0; i < 4; i++) {
      const period = 1.6 + random(`sb${i}`) * 1.2;
      const phase = (t + random(`so${i}`) * 4) % period;
      if (phase > 0.5) continue;
      const x = 1150 + random(`sx${i}${Math.floor((t + random(`so${i}`) * 4) / period)}`) * 900;
      const u = phase / 0.5;
      flashes.push(
        <g key={`s${i}`} opacity={1 - u}>
          <circle cx={x} cy={GROUND - 40} r={60 + 140 * u} fill="url(#flashGlow)" />
          <circle cx={x} cy={GROUND - 60 - 80 * u} r={40 + 70 * u} fill="#3a3a40" opacity={0.7} />
        </g>
      );
    }
  }
  // star shell drifting down over the lines in the hook
  const flareU = (t - 0.2) / 6;
  const flare = flareU > 0 && flareU < 1 ? { x: lerp(1400, 1800, flareU), y: lerp(300, 900, flareU ** 1.6), a: Math.sin(Math.PI * flareU) } : null;

  // --- candle trees on the German parapet ---
  const treesLit = ramp(t, S("trees") + 2.0, W("trees", "Small") + 1.2, Easing.linear);
  const treesVisible = t < S("orders") + 1 || t >= S("outro");
  const treeXs = [1960, 2060, 2150, 2240, 2640];

  // --- people ---
  const people: React.ReactNode[] = [];
  const outOfTrench = t >= S("morning") && t < S("war") - 0.2;
  // trench garrisons peeking (night scenes) - hidden while men are out
  if (!outOfTrench && t < S("war") + 0.5 || t >= S("outro")) {
    const peek = (side: "gb" | "de", x: number, i: number) => {
      const up = Math.sin(t * 0.7 + i) * 4;
      people.push(<Soldier key={`p${side}${i}`} side={side} x={x} y={STEP_Y + up} facing={side === "gb" ? 1 : -1} pose={{ armL: 70, armR: 80 }} />);
    };
    [760, 840].forEach((x, i) => peek("gb", x, i));
    [2420, 2500].forEach((x, i) => peek("de", x, i));
  }

  // morning: first men climb out, hands open
  const climbGB = ramp(t, W("morning", "climb") - 0.3, W("morning", "climb") + 1.4);
  const climbDE = ramp(t, W("morning", "climb") + 0.3, W("morning", "climb") + 2.0);
  // meet: everyone walks to the middle
  const meetU = ramp(t, S("meet") - 0.2, W("meet", "shake") - 0.1, Easing.inOut(Easing.quad));
  if (outOfTrench) {
    const shaking = t > W("meet", "shake") - 0.1 && t < S("bury");
    const crowd = t >= S("meet") - 0.2 ? [0, 1, 2] : [0];
    for (const side of ["gb", "de"] as const) {
      const sgn = side === "gb" ? 1 : -1;
      const trenchEdge = side === "gb" ? GB_TRENCH[1] - 40 : DE_TRENCH[0] + 40;
      const climb = side === "gb" ? climbGB : climbDE;
      crowd.forEach((k) => {
        const lead = k === 0;
        // start: climbing up out of the trench onto the parapet
        const startX = trenchEdge + sgn * 20 - sgn * k * 60;
        const climbY = lerp(STEP_Y, GROUND, climb);
        const midX = 1600 - sgn * (lead ? 34 : 120 + k * 70);
        let x = lerp(startX + sgn * 50 * climb, midX, k === 0 ? meetU : ramp(t, S("meet") + k * 0.4, W("meet", "shake") + k * 0.3, Easing.inOut(Easing.quad)));
        let y = k === 0 ? (t < S("meet") ? climbY : GROUND) : GROUND;
        if (k > 0 && t < S("meet") + k * 0.4) {
          // later men pop up out of the trench
          y = lerp(STEP_Y, GROUND, ramp(t, S("meet") - 0.3 + k * 0.3, S("meet") + 0.6 + k * 0.3));
          x = startX;
        }
        const moving = (k === 0 ? meetU > 0 && meetU < 1 : x !== midX && t > S("meet")) && t < W("meet", "shake") + k * 0.3;
        const wavePose = t < S("meet") && lead ? { armL: 150 + Math.sin(t * 6) * 10, armR: 160 } : undefined;
        let pose: Pose = moving ? { walk: t * 7 + k } : wavePose ?? { armL: 6, armR: 10 };
        if (lead && shaking) pose = { armL: 4, armR: 62 + Math.sin(t * 10) * 6 };
        if (t >= S("bury") && t < S("football")) pose = { armL: 4, armR: 30, bow: 1, capOff: true };
        if (t >= S("football") && t < S("lasts")) {
          // a kick-about: players drift around the ball
          x = midX + sgn * -40 * Math.sin(t * 1.3 + k);
          pose = { walk: t * 6 + k };
        }
        people.push(<Soldier key={`${side}${k}`} side={side} x={x} y={y} facing={sgn as 1 | -1} pose={pose} opacity={k === 0 ? 1 : ramp(t, S("meet") - 0.3 + k * 0.3, S("meet") + k * 0.3)} />);
      });
    }
  }

  // --- swapped items flying between the two leads ---
  const items: React.ReactNode[] = [];
  const kinds = [["cigarettes", "cigarettes"], ["chocolate", "chocolate"], ["buttons", "buttons"], ["beer", "beer"]] as const;
  kinds.forEach(([kind, word], i) => {
    const at = W("meet", word);
    const u = ramp(t, at - 0.2, at + 0.7, Easing.inOut(Easing.quad));
    if (t < at - 0.2 || t > S("bury")) return;
    const fromGB = i % 2 === 0;
    const x0 = fromGB ? 1560 : 1640, x1 = fromGB ? 1650 : 1550;
    const x = lerp(x0, x1, u), y = GROUND - 120 - Math.sin(Math.PI * u) * 110;
    const settled = u >= 1;
    items.push(<Item key={kind} kind={kind} x={settled ? x1 + (fromGB ? 10 : -10) : x} y={settled ? GROUND - 70 - i * 0 : y} rot={u * 360 * (fromGB ? 1 : -1) * (settled ? 0 : 1)} s={1.3} />);
  });

  // --- graves ---
  // graves fade before the football so the ball never goes over them
  const graves = ramp(t, S("bury") + 0.2, S("bury") + 1.4) * (1 - ramp(t, S("football") - 0.4, S("football") + 0.2));
  const graveEls = graves > 0 && t < S("war")
    ? [1490, 1560, 1640, 1710].map((x, i) => (
        <g key={x} opacity={Math.min(1, graves * 4 - i)} transform={`translate(${x},${GROUND + 2})`}>
          <ellipse cx={0} cy={4} rx={38} ry={9} fill="#4d463c" />
          <rect x={-3.5} y={-58} width={7} height={60} fill="#5a4630" />
          <rect x={-18} y={-44} width={36} height={7} fill="#5a4630" />
        </g>
      ))
    : null;

  // --- football ---
  let ball: React.ReactNode = null;
  if (t >= S("football") - 0.1 && t < S("lasts")) {
    const tt = t - S("football");
    const hop = 0.75;
    const n = Math.floor(tt / hop), u = (tt % hop) / hop;
    const xs = [1520, 1690, 1560, 1700, 1500, 1660, 1580, 1720];
    const x = lerp(xs[n % xs.length], xs[(n + 1) % xs.length], u);
    const y = GROUND - 14 - Math.sin(Math.PI * u) * (90 + (n % 3) * 30);
    ball = <Football x={x} y={y} rot={tt * 400} />;
  }
  // caps for goalposts
  const posts = t >= S("football") && t < S("lasts")
    ? [1420, 1470, 1740, 1790].map((x) => <path key={x} d={`M${x - 12},${GROUND} Q${x},${GROUND - 14} ${x + 12},${GROUND}Z`} fill="#4a4436" />)
    : null;

  // --- carols: notes rising from each trench ---
  const notes: React.ReactNode[] = [];
  const singing = (side: "gb" | "de", from: number, to: number, color: string) => {
    if (t < from || t > to + 3) return;
    for (let i = 0; i < 14; i++) {
      const born = from + i * 0.55;
      const age = t - born;
      if (age < 0 || age > 3.2 || born > to) continue;
      const baseX = side === "de" ? 2400 + (i % 5) * 45 : 740 + (i % 5) * 45;
      const x = baseX + Math.sin(age * 2 + i) * 30 + (side === "de" ? -age * 40 : age * 40);
      const y = GROUND - 80 - age * 120;
      notes.push(<Note key={`${side}${i}`} x={x} y={y} s={1.5} color={color} opacity={Math.min(1, age * 2) * (1 - age / 3.2)} double={i % 3 === 1} />);
    }
  };
  singing("de", W("sing", "begin"), E("sing") - 0.3, "#ffe6a6");
  singing("gb", W("answer", "carols") - 0.4, E("answer"), "#bfe3ff");
  singing("de", W("answer", "Song") + 0.4, E("answer"), "#ffe6a6");

  // --- war resumes: smoke and the trees are gone ---
  const smoke = t > S("war") - 0.3 && t < E("war") + 0.5
    ? Array.from({ length: 10 }, (_, i) => {
        const x = 900 + random(`sm${i}`) * 1400, s = ((t * 0.3 + random(`smo${i}`)) % 1);
        return <circle key={i} cx={x + s * 60} cy={GROUND - 80 - s * 300} r={60 + s * 120} fill="#2c2a2e" opacity={0.45 * (1 - s)} />;
      })
    : null;

  const vb = 1080 / cam.z;
  return (
    <svg width={1080} height={1920} viewBox={`${cam.cx - vb / 2} ${cam.cy - (vb * 16) / 9 / 2} ${vb} ${(vb * 16) / 9}`} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={skyTop} />
          <stop offset="1" stopColor={skyBot} />
        </linearGradient>
        <radialGradient id="flashGlow">
          <stop offset="0" stopColor="#fff2b8" stopOpacity="0.95" />
          <stop offset="0.35" stopColor="#ffb347" stopOpacity="0.5" />
          <stop offset="1" stopColor="#ff8a3d" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="candleGlow">
          <stop offset="0" stopColor="#ffe3a0" stopOpacity="0.85" />
          <stop offset="1" stopColor="#ffb85c" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="flareGlow">
          <stop offset="0" stopColor="#f4fbff" stopOpacity="0.9" />
          <stop offset="0.2" stopColor="#cfe6ff" stopOpacity="0.35" />
          <stop offset="1" stopColor="#cfe6ff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect x={-2000} y={-3000} width={8000} height={5000} fill="url(#sky)" />
      {/* stars at night */}
      {Array.from({ length: 90 }, (_, i) => (
        <circle key={i} cx={-900 + random(`st${i}`) * 5000} cy={-1600 + random(`sty${i}`) * 2500} r={1.5 + random(`str${i}`) * 2.5} fill="#fff"
          opacity={(1 - day) * (0.4 + 0.6 * Math.abs(Math.sin(t * 0.8 + i)))} />
      ))}
      {flare && <circle cx={flare.x} cy={flare.y} r={900} fill="url(#flareGlow)" opacity={flare.a} />}
      {flare && <circle cx={flare.x} cy={flare.y} r={10} fill="#ffffff" opacity={flare.a} />}
      {/* distant ridge and shattered trees */}
      <path d={`M-1000,${GROUND - 40} Q200,${GROUND - 130} 1300,${GROUND - 70} T3200,${GROUND - 90} T4400,${GROUND - 60} L4400,${GROUND} L-1000,${GROUND}Z`}
        fill={interpolateColors(day, [0, 1], ["#141a2a", "#8d939a"])} />
      {[-300, 820, 1350, 2150, 3350].map((x, i) => (
        <path key={x} d={`M${x},${GROUND - 60} l6,-${150 + i * 20} l4,40 l10,-30 l-4,${120 + i * 20}Z`} fill={interpolateColors(day, [0, 1], ["#0d1120", "#6d7178"])} />
      ))}
      {/* ground */}
      <path d={ground} fill={groundCol} />
      <path d={ground} fill="none" stroke={snowCol} strokeWidth={10} />
      {/* earth strata */}
      {[[GROUND + 300, 90, "#00000022"], [GROUND + 470, 140, "#00000030"], [GROUND + 700, 400, "#0000003d"]].map(([y, h, c], i) => (
        <rect key={i} x={-2000} y={y as number} width={8000} height={h as number} fill={c as string} />
      ))}
      {Array.from({ length: 70 }, (_, i) => (
        <ellipse key={`r${i}`} cx={-200 + random(`rx${i}`) * 3600} cy={GROUND + 290 + random(`ry${i}`) * 600} rx={6 + random(`rr${i}`) * 16} ry={4 + random(`rq${i}`) * 8}
          fill="#00000040" />
      ))}
      {/* trench walls */}
      {[GB_TRENCH, DE_TRENCH].map(([a, b]) => (
        <g key={a}>
          <rect x={a + 20} y={GROUND} width={b - a - 40} height={260} fill={interpolateColors(day, [0, 1], ["#16161c", "#3b362e"])} />
          {Array.from({ length: Math.floor((b - a - 40) / 26) }, (_, i) => (
            <line key={i} x1={a + 30 + i * 26} y1={GROUND + 10} x2={a + 30 + i * 26} y2={GROUND + 250} stroke="#2a241c" strokeWidth={8} opacity={0.6} />
          ))}
          <rect x={a + 20} y={GROUND + 230} width={b - a - 40} height={30} fill="#3a4250" opacity={0.7} />
          <rect x={a + 30} y={STEP_Y - 4} width={b - a - 60} height={14} fill="#4a3a28" />
        </g>
      ))}
      <Sandbags x0={GB_TRENCH[1] - 10} x1={GB_TRENCH[1] + 130} rows={3} />
      <Sandbags x0={DE_TRENCH[0] - 130} x1={DE_TRENCH[0] + 10} rows={3} />
      <Wire x0={1080} x1={1290} />
      <Wire x0={1910} x1={2120} />
      {treesVisible &&
        treeXs.map((x, i) => (
          <CandleTree key={x} x={x} y={i === 3 ? GROUND - 66 : GROUND - 6} t={t} lit={t >= S("outro") ? (i === 3 ? ramp(t, S("outro"), S("outro") + 1) : 0) : Math.min(1, Math.max(0, treesLit * 5 - i))}
            scale={1.25} seed={i} />
        ))}
      {graveEls}
      {posts}
      {people}
      {items}
      {ball}
      {notes}
      {smoke}
      {flashes}
      {/* mourning: wash out colour */}
      <rect x={-2000} y={-3000} width={8000} height={6000} fill="#7d8088" opacity={0.35 * mourn} style={{ mixBlendMode: "saturation" }} />
    </svg>
  );
};
