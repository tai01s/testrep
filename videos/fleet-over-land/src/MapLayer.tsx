import React, { useMemo } from "react";
import { Easing, interpolate, random } from "remotion";
import {
  ASIA, CHAIN_A, HORN_INNER, CHAIN_B, CITY, EUROPE, GALATA, GALATA_TOWER, HAGIA_SOPHIA, HORN, HORN_NORTH, HORN_SOUTH, HORN_WALLS,
  LAND_WALLS, MARMARA_WALLS, Pt, ROUTE, ROUTE_LAND, along, inPolygon, partialPath, smooth,
} from "./geo";
import { BYZANTINE, OTTOMAN, Ship } from "./Ship";
import { E, S, W } from "./timeline";
import { Cam } from "./camera";
import { fonts } from "./fonts";

const C = {
  water: "#123b52",
  waterLight: "#1d5370",
  land: "#e4d0a0",
  asia: "#d8c290",
  shore: "#9c7c4a",
  city: "#efdcb0",
  wall: "#7d5c3a",
  ink: "#2b1d10",
};

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.33, 0, 0.2, 1);
/** 0..1 ramp between two times */
const ramp = (t: number, a: number, b: number, easing = ease) => interpolate(t, [a, b], [0, 1], { ...clamp, easing });

// ---------- static decoration, generated once ----------
const useCityBlocks = () =>
  useMemo(() => {
    const out: { x: number; y: number; w: number; h: number; r: number; c: string }[] = [];
    let i = 0;
    while (out.length < 420 && i < 6000) {
      const p: Pt = [180 + random(`bx${i}`) * 560, 340 + random(`by${i}`) * 580];
      i++;
      if (!inPolygon(p, CITY)) continue;
      out.push({
        x: p[0], y: p[1], w: 4 + random(`bw${i}`) * 6, h: 3 + random(`bh${i}`) * 4, r: random(`br${i}`) * 90,
        c: random(`bc${i}`) > 0.5 ? "#c9a878" : "#d9bb8a",
      });
    }
    return out;
  }, []);

// ---------- labels with constant on-screen size ----------
const Label: React.FC<{
  x: number; y: number; text: string; px: number; cam: Cam; color?: string; opacity?: number; rotate?: number;
  weight?: number; spacing?: number; font?: string; halo?: string;
}> = ({ x, y, text, px, cam, color = C.ink, opacity = 1, rotate = 0, weight = 700, spacing = 0.12, font = fonts.title, halo = "rgba(245,232,200,0.85)" }) => {
  if (opacity <= 0.001) return null;
  const size = (px * cam.w) / 1080;
  return (
    <text
      x={x} y={y} fontSize={size} fill={color} opacity={opacity} fontFamily={font} fontWeight={weight}
      textAnchor="middle" dominantBaseline="middle" letterSpacing={size * spacing}
      transform={rotate ? `rotate(${rotate},${x},${y})` : undefined}
      stroke={halo} strokeWidth={size * 0.18} paintOrder="stroke" strokeLinejoin="round"
    >
      {text}
    </text>
  );
};

// ---------- fleets ----------
const ANCHOR: Pt[] = Array.from({ length: 16 }, (_, i) => [818 + (i % 3) * 22 + (i % 2) * 6, 300 + Math.floor(i / 3) * 34 + (i % 3) * 9] as Pt);
const PARK: Pt[] = Array.from({ length: 22 }, (_, i) => {
  // three loose rows inside the Golden Horn, west of the Byzantine ships
  const row = i % 3, col = Math.floor(i / 3);
  const x = 380 + col * 26 + row * 9;
  const centre = interpolate(x, [380, 450, 520, 580], [420, 465, 505, 539]);
  return [x, centre + (row - 1) * 15] as Pt;
});
const BYZ: Pt[] = [[628, 572], [612, 556], [646, 592], [596, 540], [660, 606]];
const HORN_ANGLE = 32; // pointing east-southeast, toward the mouth

const DRAG_GAP = 0.3; // seconds between ships entering the route
const DRAG_TRAVEL = 3.6; // seconds to cross the hill

export const MapLayer: React.FC<{ t: number; cam: Cam }> = ({ t, cam }) => {
  const blocks = useCityBlocks();
  const vb = `${cam.cx - cam.w / 2} ${cam.cy - (cam.w * 16) / 9 / 2} ${cam.w} ${(cam.w * 16) / 9}`;
  const px = cam.w / 1080; // world units per screen pixel

  // --- timing ---
  const surround = ramp(t, W("setup", "surrounded") - 0.3, W("setup", "surrounded") + 1.4);
  const armyIn = ramp(t, S("setup") + 0.6, S("setup") + 3.5);
  const hornGlow = ramp(t, W("chain", "Golden") - 0.2, W("chain", "Golden") + 0.6) * (1 - ramp(t, E("chain") + 0.5, E("chain") + 1.2));
  const chainDraw = t < S("setup") ? 1 : ramp(t, W("chain", "chain") - 0.2, W("chain", "chain") + 0.9);
  const routeDraw = ramp(t, S("road") + 0.4, W("road", "behind") + 0.6, Easing.inOut(Easing.quad));
  const planks = ramp(t, S("road") + 0.8, W("road", "grease") - 0.2, Easing.linear);
  const grease = ramp(t, W("road", "grease") - 0.1, W("road", "grease") + 0.6);
  const routePreview = ramp(t, S("twist") + 0.5, S("twist") + 2.2) * (1 - ramp(t, S("road"), S("road") + 0.5));
  const dawn = ramp(t, S("reveal") - 0.2, S("reveal") + 1.5) * (1 - ramp(t, S("stretch") + 0.5, S("stretch") + 2));
  const seaFront = ramp(t, S("stretch") + 0.3, S("stretch") + 1.2) * (1 - ramp(t, S("fall") + 0.2, S("fall") + 1));
  const defendersMove = ramp(t, W("stretch", "guarding") - 0.4, W("stretch", "stretched") + 0.4, Easing.inOut(Easing.cubic));
  const fallen = ramp(t, W("fall", "falls") - 0.1, W("fall", "falls") + 0.9);
  const flagsUp = ramp(t, W("fall", "falls") + 0.1, W("fall", "falls") + 1.2);

  // --- Ottoman ships: anchored, attacking, dragged, parked ---
  const ships: React.ReactNode[] = [];
  const dragStart = S("drag") - 0.2;
  const departed = t < dragStart ? 0 : Math.min(ANCHOR.length, Math.floor((t - dragStart) / DRAG_GAP) + 1);
  const afterDrag = t >= S("reveal") - 0.1;
  const fleetIn = ramp(t, S("setup") + 1.2, S("setup") + 3);

  ANCHOR.forEach(([x, y], i) => {
    if (afterDrag || i >= ANCHOR.length - departed) return;
    const bob = Math.sin(t * 1.6 + i) * 0.8;
    ships.push(<Ship key={`a${i}`} x={x} y={y + bob} angle={100 + (i % 4) * 6} t={t} rowing={false} opacity={t < S("setup") ? 1 : fleetIn} />);
  });

  // failed attack on the chain
  const failT = t - S("fail");
  if (t > S("chain") + 2 && t < S("twist") + 1.5) {
    for (let k = 0; k < 4; k++) {
      const s = 0.18 + k * 0.2;
      const target: Pt = [CHAIN_A[0] + (CHAIN_B[0] - CHAIN_A[0]) * s + 15, CHAIN_A[1] + (CHAIN_B[1] - CHAIN_A[1]) * s];
      const start: Pt = [target[0] + 95, target[1] + 30 - k * 6];
      const charge = ramp(failT, -0.4 + k * 0.08, 0.75 + k * 0.08, Easing.in(Easing.quad));
      const bounce = ramp(failT, 0.8 + k * 0.08, 2.0 + k * 0.08, Easing.out(Easing.back(2)));
      const x = start[0] + (target[0] - start[0]) * charge + 32 * bounce;
      const y = start[1] + (target[1] - start[1]) * charge + 9 * bounce;
      const wobble = Math.sin(failT * 18) * 14 * Math.max(0, 1 - Math.abs(failT - 1.0 - k * 0.08) * 2);
      const appear = ramp(t, S("chain") + 2, S("chain") + 2.8) * (1 - ramp(t, S("twist") + 0.6, S("twist") + 1.4));
      ships.push(<Ship key={`f${k}`} x={x} y={y} angle={198 + wobble} t={t} wake={charge > 0 && charge < 1 ? 1 : 0} opacity={appear} />);
    }
  }

  // dragged over the hill, then parked inside the Horn
  if (t >= dragStart) {
    const n = afterDrag ? PARK.length : departed;
    for (let k = 0; k < n; k++) {
      const p = afterDrag ? 2 : (t - dragStart - k * DRAG_GAP) / DRAG_TRAVEL;
      const park = PARK[k];
      if (p < 1) {
        const pos = along(ROUTE, p);
        const onLand = p > ROUTE_LAND[0] && p < ROUTE_LAND[1];
        ships.push(<Ship key={`d${k}`} x={pos.x} y={pos.y} angle={pos.angle} t={t} rollers={onLand} rowing wake={onLand ? 0 : 1} />);
      } else {
        const end = along(ROUTE, 1);
        const u = afterDrag ? 1 : ramp(p, 1, 1 + 0.9 / DRAG_TRAVEL);
        const x = end.x + (park[0] - end.x) * u, y = end.y + (park[1] - end.y) * u;
        const ang = interpolate(u, [0, 1], [end.angle, HORN_ANGLE]);
        ships.push(<Ship key={`d${k}`} x={x} y={y + Math.sin(t * 1.5 + k) * 0.6} angle={ang} t={t} wake={u < 1 ? 1 : 0} rowing={u < 1} />);
      }
    }
  }

  // Byzantine ships guarding behind the chain
  BYZ.forEach(([x, y], i) => {
    const alarm = ramp(t, W("reveal", "wake") + i * 0.1, W("reveal", "wake") + 0.4 + i * 0.1);
    ships.push(<Ship key={`b${i}`} x={x} y={y + Math.sin(t * 1.3 + i) * 0.6} angle={200 - alarm * 25} t={t} colors={BYZANTINE} rowing={false} scale={0.95} opacity={1 - fallen} />);
  });

  // --- defenders on the walls (stretch scene) ---
  const defenders: React.ReactNode[] = [];
  if (t > S("stretch") - 0.5 && t < E("fall") + 1) {
    const vis = ramp(t, S("stretch") + 0.1, S("stretch") + 0.9) * (1 - fallen);
    for (let i = 0; i < 26; i++) {
      const s = (i + 0.5) / 26;
      const home = along(LAND_WALLS, s);
      const moves = i % 5 !== 0 && i % 5 !== 3; // 3 of every 5 have to leave
      const dest = along(HORN_WALLS, (i * 0.37) % 1);
      const d = moves ? ramp(defendersMove, i * 0.012, 0.6 + i * 0.012) : 0;
      const x = home.x + (dest.x + 6 - home.x) * d, y = home.y + (dest.y + 4 - home.y) * d;
      defenders.push(<circle key={i} cx={x} cy={y} r={5} fill="#5d7bd8" stroke="#f1f4ff" strokeWidth={1.4} opacity={vis} />);
    }
  }

  // --- route geometry ---
  const routePath = partialPath(ROUTE, routeDraw);
  const plankEls: React.ReactNode[] = [];
  const nPlanks = 46;
  for (let i = 0; i < nPlanks; i++) {
    const s = ROUTE_LAND[0] - 0.02 + ((ROUTE_LAND[1] - ROUTE_LAND[0] + 0.04) * i) / (nPlanks - 1);
    const shown = ramp(planks, i / nPlanks, i / nPlanks + 0.05);
    if (shown <= 0) continue;
    const p = along(ROUTE, s);
    plankEls.push(
      <rect key={i} x={-1.6} y={-9 * shown} width={3.2} height={18 * shown} rx={0.8} fill="#a8723c" stroke="#4a2c14" strokeWidth={0.5}
        transform={`translate(${p.x},${p.y}) rotate(${p.angle})`} />
    );
  }

  const tents = useMemo(
    () => Array.from({ length: 70 }, (_, i) => ({ x: 40 + random(`tx${i}`) * 140, y: 330 + random(`ty${i}`) * 560, s: 0.7 + random(`ts${i}`) * 0.6, d: random(`td${i}`) })),
    []
  );

  const cityTint = interpolate(fallen, [0, 1], [0, 0.42]);
  const surroundPath = useMemo(() => [
    [250, 300], [180, 360], [150, 520], [140, 700], [150, 880], [260, 960], [520, 900], [760, 800], [850, 640], [830, 470], [760, 330], [600, 250], [420, 250],
  ] as Pt[], []);

  return (
    <svg width={1080} height={1920} viewBox={vb} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <pattern id="waves" width="60" height="30" patternUnits="userSpaceOnUse" patternTransform={`translate(${(t * 6) % 60},0)`}>
          <path d="M0,15 Q15,8 30,15 T60,15" stroke="#5f97b5" strokeWidth="1.2" fill="none" opacity="0.5" />
        </pattern>
        <radialGradient id="hill">
          <stop offset="0%" stopColor="#b39563" stopOpacity="0.75" />
          <stop offset="100%" stopColor="#b39563" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="spot">
          <stop offset="0%" stopColor="#ffe9a8" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#ffe9a8" stopOpacity="0" />
        </radialGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" />
        </filter>
        <linearGradient id="greaseGrad" gradientUnits="userSpaceOnUse" x1={480 + ((t * 160) % 420)} y1="0" x2={560 + ((t * 160) % 420)} y2="0">
          <stop offset="0" stopColor="#fff6c8" stopOpacity="0" />
          <stop offset="0.5" stopColor="#fff6c8" stopOpacity="0.95" />
          <stop offset="1" stopColor="#fff6c8" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* water */}
      <rect x={-2000} y={-2000} width={5000} height={5000} fill={C.water} />
      <rect x={-2000} y={-2000} width={5000} height={5000} fill="url(#waves)" />

      {/* land */}
      <path d={smooth(ASIA, true)} fill={C.asia} stroke={C.shore} strokeWidth={2.5} />
      <path d={smooth(EUROPE, true)} fill={C.land} stroke={C.shore} strokeWidth={2.5} />
      <path d={smooth(HORN, true)} fill={C.water} />
      <path d={smooth(HORN, true)} fill="url(#waves)" />
      <path d={smooth(HORN_INNER, true)} fill="#62d6ff" opacity={0.38 * hornGlow * (0.75 + 0.25 * Math.sin(t * 6))} />
      <path d={smooth(HORN_NORTH)} fill="none" stroke={C.shore} strokeWidth={2.5} />
      <path d={smooth(HORN_SOUTH)} fill="none" stroke={C.shore} strokeWidth={2.5} />

      {/* hills behind Galata */}
      {[[650, 372, 120, 64], [560, 340, 80, 55], [735, 320, 70, 70], [610, 290, 90, 50]].map(([x, y, rx, ry], i) => (
        <g key={i}>
          <ellipse cx={x} cy={y} rx={rx} ry={ry} fill="url(#hill)" />
          <ellipse cx={x} cy={y} rx={rx * 0.6} ry={ry * 0.55} fill="none" stroke="#a88a58" strokeWidth={1.2} strokeDasharray="4 4" opacity={0.6} />
          <ellipse cx={x} cy={y} rx={rx * 0.3} ry={ry * 0.27} fill="none" stroke="#a88a58" strokeWidth={1.2} strokeDasharray="4 4" opacity={0.6} />
        </g>
      ))}

      {/* city */}
      <path d={smooth(CITY, true)} fill={C.city} />
      {blocks.map((b, i) => (
        <rect key={i} x={b.x} y={b.y} width={b.w} height={b.h} fill={b.c} transform={`rotate(${b.r},${b.x},${b.y})`} opacity={0.9} />
      ))}
      <path d={smooth(CITY, true)} fill="#c0281e" opacity={cityTint} />
      {/* Hagia Sophia */}
      <g transform={`translate(${HAGIA_SOPHIA[0]},${HAGIA_SOPHIA[1]})`}>
        <rect x={-14} y={-6} width={28} height={16} fill="#c99a5b" stroke={C.ink} strokeWidth={1} />
        <path d="M-10,-6 A10,10 0 0 1 10,-6Z" fill="#8fa9b8" stroke={C.ink} strokeWidth={1} />
      </g>

      {/* walls */}
      <path d={smooth(MARMARA_WALLS)} fill="none" stroke={C.wall} strokeWidth={3.5} />
      <path d={smooth(HORN_WALLS)} fill="none" stroke={C.wall} strokeWidth={3.5} />
      <path d={smooth(HORN_WALLS)} fill="none" stroke="#ff3b2f" strokeWidth={9} opacity={seaFront * (0.55 + 0.45 * Math.sin(t * 8))} filter="url(#glow)" />
      <path d={smooth(HORN_WALLS)} fill="none" stroke="#ff5a3c" strokeWidth={4} opacity={seaFront} />
      <path d={smooth(LAND_WALLS)} fill="none" stroke={C.wall} strokeWidth={7} />
      <path d={smooth(LAND_WALLS)} fill="none" stroke="#3a2a18" strokeWidth={7} strokeDasharray="3 9" />

      {/* Galata */}
      <path d={smooth(GALATA, true)} fill="#ead7a9" stroke={C.wall} strokeWidth={2.5} />
      <circle cx={GALATA_TOWER[0]} cy={GALATA_TOWER[1]} r={5} fill="#a77c4a" stroke={C.ink} strokeWidth={1.2} />

      {/* Ottoman camp outside the land walls */}
      {tents.map((tn, i) =>
        armyIn > tn.d ? (
          <path key={i} d={`M${tn.x - 5 * tn.s},${tn.y + 3 * tn.s} L${tn.x},${tn.y - 5 * tn.s} L${tn.x + 5 * tn.s},${tn.y + 3 * tn.s}Z`}
            fill="#c8352a" stroke="#5a120c" strokeWidth={0.8} opacity={Math.min(1, (armyIn - tn.d) * 8)} />
        ) : null
      )}
      <path d={partialPath(useMemo(() => [...surroundPath, surroundPath[0]], [surroundPath]), surround)} fill="none" stroke="#e23b2e"
        strokeWidth={6} strokeDasharray="18 12" strokeLinecap="round" opacity={0.9 * (1 - ramp(t, S("chain") + 0.3, S("chain") + 1))} />

      {/* the overland road */}
      {routePreview > 0 && (
        <path d={partialPath(ROUTE, routePreview)} fill="none" stroke="#ffe08a" strokeWidth={5} strokeDasharray="10 10"
          strokeDashoffset={-t * 40} opacity={0.5 + 0.5 * Math.sin(t * 6)} strokeLinecap="round" />
      )}
      {routeDraw > 0 && <path d={routePath} fill="none" stroke="#7a5230" strokeWidth={22} strokeLinecap="round" opacity={0.35} />}
      {plankEls}
      {grease > 0 && (
        <path d={partialPath(ROUTE, ROUTE_LAND[1])} fill="none" stroke="url(#greaseGrad)" strokeWidth={14} strokeLinecap="round" opacity={grease * (t < S("reveal") ? 1 : 0.3)} />
      )}

      {/* the chain */}
      <Chain draw={chainDraw} t={t} highlight={hornGlow} />

      {defenders}
      {ships}

      {/* Ottoman flags once the city falls */}
      {flagsUp > 0 &&
        [HAGIA_SOPHIA, [212, 540], [204, 690], [222, 420], [420, 640], [540, 720], [600, 600]].map(([x, y], i) => {
          const u = ramp(flagsUp, i * 0.1, i * 0.1 + 0.4, Easing.out(Easing.back(3)));
          return (
            <g key={i} transform={`translate(${x},${y - 6}) scale(${u})`}>
              <line x1={0} y1={0} x2={0} y2={-30} stroke={C.ink} strokeWidth={2} />
              <path d={`M0,-30 Q10,${-33 + Math.sin(t * 6 + i) * 2} 20,-30 L20,-18 Q10,-15 0,-18Z`} fill="#d7261e" stroke="#5a120c" strokeWidth={1} />
            </g>
          );
        })}

      {/* dawn light over the harbour */}
      <rect x={-2000} y={-2000} width={5000} height={5000} fill="#ff9d4d" opacity={0.18 * dawn} style={{ mixBlendMode: "multiply" }} />

      {/* labels */}
      <Label x={450} y={590} text="CONSTANTINOPLE" px={50} cam={cam} opacity={1 - fallen * 0.6} />
      <Label x={450} y={590 + 48 * px} text="ISTANBUL" px={34} cam={cam} color="#9b1d14" opacity={ramp(t, W("fall", "falls") + 0.8, W("fall", "falls") + 1.6)} />
      <Label x={432} y={452} text="GOLDEN HORN" px={30} cam={cam} rotate={31} color="#e9f7ff" halo="rgba(10,40,60,0.9)" opacity={t < S("setup") + 0.5 ? 0 : 0.85 + 0.15 * hornGlow} />
      <Label x={655} y={430} text="GALATA" px={30} cam={cam} opacity={ramp(t, S("setup") + 1, S("setup") + 2)} />
      <Label x={850} y={-40} text="BOSPHORUS" px={30} cam={cam} rotate={-84} color="#e9f7ff" halo="rgba(10,40,60,0.9)" />
      <Label x={470} y={1010} text="SEA OF MARMARA" px={32} cam={cam} color="#e9f7ff" halo="rgba(10,40,60,0.9)" />
      <Label x={1010} y={640} text="ASIA" px={30} cam={cam} />
      <Label x={95} y={250} text="OTTOMAN ARMY" px={28} cam={cam} color="#9b1d14" opacity={armyIn * (1 - fallen)} />
      <Label x={CHAIN_A[0] + 46 * px * 2.2} y={CHAIN_A[1] + 30} text="THE CHAIN" px={26} cam={cam} color="#2b1d10"
        opacity={ramp(t, W("chain", "chain"), W("chain", "chain") + 0.4) * (1 - ramp(t, S("twist"), S("twist") + 0.5)) + ramp(t, W("reveal", "Behind"), W("reveal", "Behind") + 0.3)} />
      <Label x={640} y={300} text="THE HILLS" px={28} cam={cam} opacity={ramp(t, W("road", "hills"), W("road", "hills") + 0.4) * (1 - ramp(t, S("drag") + 1, S("drag") + 2))} />
      <Label x={330} y={448} text="NEW FRONT" px={30} cam={cam} rotate={31} color="#c0281e" opacity={seaFront} />
      <Label x={830} y={250} text="OTTOMAN FLEET" px={24} cam={cam} color="#9b1d14" halo="rgba(245,232,200,0.9)" opacity={ramp(t, S("setup") + 2, S("setup") + 3) * (1 - ramp(t, S("chain"), S("chain") + 0.6))} />
      <Label x={440} y={392} text="OTTOMAN SHIPS!" px={30} cam={cam} color="#c0281e" opacity={ramp(t, W("reveal", "enemy"), W("reveal", "enemy") + 0.3) * (1 - ramp(t, S("stretch"), S("stretch") + 0.5))} />
    </svg>
  );
};

const Chain: React.FC<{ draw: number; t: number; highlight: number }> = ({ draw, t, highlight }) => {
  if (draw <= 0) return null;
  const links: React.ReactNode[] = [];
  const n = 26;
  const [ax, ay] = CHAIN_A, [bx, by] = CHAIN_B;
  const ang = (Math.atan2(by - ay, bx - ax) * 180) / Math.PI;
  for (let i = 0; i < n * draw; i++) {
    const s = i / (n - 1);
    const sag = Math.sin(s * Math.PI) * 6 + Math.sin(t * 2 + i * 0.6) * 0.6;
    const x = ax + (bx - ax) * s + sag * 0.9, y = ay + (by - ay) * s - sag * 0.2;
    links.push(
      <g key={i} transform={`translate(${x},${y}) rotate(${ang})`}>
        {i % 4 === 0 && <rect x={-4} y={-4.5} width={8} height={9} rx={1.5} fill="#8a5a2c" stroke="#3b2210" strokeWidth={0.6} />}
        <ellipse rx={2.6} ry={i % 2 ? 1.1 : 1.8} fill="none" stroke="#2d2d33" strokeWidth={1.5} />
        <ellipse rx={2.6} ry={i % 2 ? 1.1 : 1.8} fill="none" stroke="#aab1bd" strokeWidth={0.6} />
      </g>
    );
  }
  return (
    <g>
      <line x1={ax} y1={ay} x2={ax + (bx - ax) * draw} y2={ay + (by - ay) * draw} stroke="#ffd36b" strokeWidth={10} opacity={0.35 * highlight} filter="url(#glow)" />
      {links}
      <rect x={ax - 5} y={ay - 9} width={10} height={10} fill="#8b6b45" stroke="#2b1d10" strokeWidth={1} />
      <rect x={bx - 5} y={by - 2} width={10} height={10} fill="#8b6b45" stroke="#2b1d10" strokeWidth={1} />
    </g>
  );
};
