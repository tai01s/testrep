import React from "react";
import { Easing, interpolate } from "remotion";
import { fonts } from "./fonts";

// Schematic map of the Western Front, winter 1914 (lat/lon of towns along the line).
const K = 150;
const P = (lat: number, lon: number): [number, number] => [(lon - 1.25) * K, (51.75 - lat) * K * 1.556];

const FRONT = [
  [51.13, 2.75], [51.03, 2.86], [50.9, 2.95], [50.87, 3.0], [50.8, 2.94], [50.69, 2.9], [50.53, 2.81], [50.29, 2.8],
  [50.0, 2.7], [49.7, 2.8], [49.55, 3.0], [49.42, 3.35], [49.32, 4.03], [49.22, 4.9], [49.22, 5.45], [48.92, 5.55],
  [48.9, 6.05], [48.6, 6.6], [48.2, 7.0], [47.8, 7.1], [47.5, 7.15],
].map(([a, b]) => P(a, b));

// coast: English Channel up to the Scheldt; everything left/above it is sea
const COAST = [[49.7, 0.2], [50.4, 1.55], [50.73, 1.6], [50.95, 1.85], [51.03, 2.37], [51.13, 2.75], [51.23, 2.92], [51.33, 3.2], [51.45, 3.57], [51.9, 4.0]].map(([a, b]) => P(a, b));

const TOWNS: { name: string; at: [number, number]; key?: boolean; dx?: number }[] = [
  { name: "Ypres", at: P(50.85, 2.88), key: true },
  { name: "Arras", at: P(50.29, 2.78) },
  { name: "Reims", at: P(49.26, 4.03) },
  { name: "Verdun", at: P(49.16, 5.38) },
  { name: "Paris", at: P(48.86, 2.35), dx: -10 },
];

const len = (pts: [number, number][]) => pts.reduce((s, p, i) => (i ? s + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0), 0);
const FRONT_LEN = len(FRONT as [number, number][]);
const toPath = (pts: number[][]) => pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");

export const FrontMap: React.FC<{ local: number; dur: number }> = ({ local, dur }) => {
  const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
  const draw = interpolate(local, [0.4, 3.2], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const ypres = interpolate(local, [3.0, 3.6], [0, 1], { ...clamp, easing: Easing.out(Easing.back(2)) });
  const zoom = interpolate(local, [0, dur], [1, 1.12], clamp);
  const label = (txt: string, x: number, y: number, size: number, color: string, op = 1, spacing = 6) => (
    <text x={x} y={y} fontFamily={fonts.title} fontWeight={700} fontSize={size} fill={color} opacity={op} textAnchor="middle" letterSpacing={spacing}>
      {txt}
    </text>
  );
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <radialGradient id="mapVig" cx="50%" cy="48%" r="70%">
          <stop offset="60%" stopColor="#000" stopOpacity="0" />
          <stop offset="100%" stopColor="#000" stopOpacity="0.6" />
        </radialGradient>
      </defs>
      <rect width={1080} height={1920} fill="#d9ccb0" />
      <g transform={`translate(540,1000) scale(${zoom}) translate(-470,-500)`}>
        {/* sea */}
        <path d={`${toPath([[-400, -400], [-400, COAST[0][1]], ...COAST, [1200, -400]])}Z`} fill="#8fa7ad" />
        <path d={toPath(COAST)} stroke="#5d6f72" strokeWidth={3} fill="none" />
        {label("NORTH SEA", 330, 60, 30, "#e9f1f2", 0.9)}
        {/* sides */}
        {label("BRITISH & FRENCH", 140, 640, 26, "#3b3a5e", 0.85, 3)}
        {label("GERMAN", 760, 420, 30, "#4a4a40", 0.85, 6)}
        {/* front line */}
        <path d={toPath(FRONT)} stroke="#7a1d14" strokeWidth={9} fill="none" strokeLinejoin="round" strokeLinecap="round" opacity={0.25}
          strokeDasharray={`${FRONT_LEN * draw} ${FRONT_LEN}`} />
        <path d={toPath(FRONT)} stroke="#b3261e" strokeWidth={5} fill="none" strokeLinejoin="round" strokeLinecap="round"
          strokeDasharray={`${FRONT_LEN * draw} ${FRONT_LEN}`} />
        {TOWNS.map((tw) => (
          <g key={tw.name} opacity={draw > 0.2 ? 1 : 0}>
            <circle cx={tw.at[0]} cy={tw.at[1]} r={tw.key ? 9 : 6} fill={tw.key ? "#b3261e" : "#3a3328"} />
            <text x={tw.at[0] - 16 + (tw.dx ?? 0)} y={tw.at[1] + 8} fontFamily={fonts.title} fontWeight={700} fontSize={tw.key ? 34 : 26} fill="#2b2418" textAnchor="end">
              {tw.name}
            </text>
          </g>
        ))}
        {/* Ypres pulse */}
        <circle cx={TOWNS[0].at[0]} cy={TOWNS[0].at[1]} r={20 + 40 * ((local * 0.8) % 1)} fill="none" stroke="#b3261e" strokeWidth={4}
          opacity={ypres * (1 - ((local * 0.8) % 1))} />
        {label("SWITZERLAND", FRONT[FRONT.length - 1][0] + 40, FRONT[FRONT.length - 1][1] + 60, 24, "#4a4a40", draw > 0.95 ? 0.85 : 0, 3)}
      </g>
      <rect width={1080} height={1920} fill="url(#mapVig)" />
      <text x={540} y={330} fontFamily={fonts.title} fontWeight={900} fontSize={70} fill="#2b2418" textAnchor="middle" letterSpacing={8}>
        THE WESTERN FRONT
      </text>
      <text x={540} y={390} fontFamily={fonts.caption} fontWeight={800} fontSize={34} fill="#5a4a32" textAnchor="middle" letterSpacing={4}>
        700 KM OF TRENCHES · WINTER 1914
      </text>
    </svg>
  );
};
