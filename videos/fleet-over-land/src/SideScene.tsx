import React from "react";
import { AbsoluteFill, Easing, interpolate } from "remotion";
import { SideGalley } from "./Ship";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Ground height of the rolling hill in screen space. */
const groundY = (x: number, variant: Variant) =>
  variant === "oars" ? 1180 - (x - 540) * 0.26 + Math.sin(x / 260) * 18 : 1130 + Math.cos(((x - 560) / 900) * Math.PI) * -190;

type Variant = "walk" | "oars" | "outro";

const Sky: React.FC<{ top: string; bottom: string }> = ({ top, bottom }) => (
  <AbsoluteFill style={{ background: `linear-gradient(180deg, ${top} 0%, ${bottom} 72%)` }} />
);

const Skyline: React.FC<{ y: number; color: string; opacity?: number }> = ({ y, color, opacity = 1 }) => (
  <g opacity={opacity}>
    <g fill={color}>
      {/* walls with towers */}
      <rect x={-20} y={y - 40} width={1120} height={200} />
      {Array.from({ length: 12 }, (_, i) => (
        <rect key={i} x={i * 95 - 10} y={y - 78} width={42} height={60} />
      ))}
      {/* Hagia Sophia-like dome */}
      <path d={`M560,${y - 40} L560,${y - 120} L840,${y - 120} L840,${y - 40}Z`} />
      <path d={`M600,${y - 120} A100,100 0 0 1 800,${y - 120}Z`} />
      <path d={`M540,${y - 90} A45,45 0 0 1 630,${y - 90}Z M770,${y - 90} A45,45 0 0 1 860,${y - 90}Z`} />
      <rect x={200} y={y - 150} width={34} height={120} />
      <path d={`M190,${y - 150} L217,${y - 210} L244,${y - 150}Z`} />
    </g>
  </g>
);

const Puller: React.FC<{ x: number; y: number; t: number; i: number }> = ({ x, y, t, i }) => {
  const step = Math.sin(t * 6 + i * 1.3) * 16;
  return (
    <g transform={`translate(${x},${y})`}>
      <line x1={0} y1={-38} x2={step} y2={0} stroke="#2b1a10" strokeWidth={8} strokeLinecap="round" />
      <line x1={0} y1={-38} x2={-step} y2={0} stroke="#2b1a10" strokeWidth={8} strokeLinecap="round" />
      <line x1={0} y1={-38} x2={18} y2={-92} stroke="#8a2a1f" strokeWidth={16} strokeLinecap="round" />
      <circle cx={24} cy={-108} r={13} fill="#c98f63" />
      <ellipse cx={24} cy={-118} rx={15} ry={9} fill="#f3eee2" />
      <line x1={18} y1={-80} x2={-30} y2={-70} stroke="#2b1a10" strokeWidth={6} strokeLinecap="round" />
    </g>
  );
};

export const SideScene: React.FC<{ variant: Variant; local: number; dur: number; t: number }> = ({ variant, local, dur, t }) => {
  const fadeIn = interpolate(local, [0, 0.18], [0, 1], clamp);
  const fadeOut = interpolate(local, [dur - 0.18, dur], [1, 0], clamp);
  const opacity = Math.min(fadeIn, variant === "outro" ? 1 : fadeOut);

  if (variant === "oars") {
    // a galley crawling uphill on greased rollers, oars rowing through the air
    const travel = local * 70;
    const x = 400 + local * 18;
    const slope = Math.atan(-0.26) * (180 / Math.PI);
    const gy = groundY(x, "oars");
    return (
      <AbsoluteFill style={{ opacity }}>
        <Sky top="#f3b36b" bottom="#8fb6d1" />
        <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
          {/* distant Bosphorus and Galata tower */}
          <rect x={0} y={1000} width={1080} height={300} fill="#3f7ea3" />
          <path d="M0,1000 Q300,940 600,990 T1080,970 L1080,1080 L0,1080Z" fill="#c9b48a" />
          <g transform="translate(900,910)" fill="#7e6a52">
            <rect x={-26} y={0} width={52} height={110} />
            <path d="M-34,0 L0,-70 L34,0Z" />
          </g>
          {/* hillside */}
          <path d={`M-20,${groundY(-20, "oars")} ${Array.from({ length: 24 }, (_, i) => `L${i * 50},${groundY(i * 50, "oars")}`).join(" ")} L1100,1920 L-20,1920Z`} fill="#b58f57" />
          <path d={`M-20,${groundY(-20, "oars") + 12} ${Array.from({ length: 24 }, (_, i) => `L${i * 50},${groundY(i * 50, "oars") + 12}`).join(" ")}`} stroke="#8a6436" strokeWidth={10} fill="none" />
          {/* planks of the wooden road */}
          {Array.from({ length: 30 }, (_, i) => {
            const px = ((i * 52 - travel * 0) % 1600) - 100;
            return <rect key={i} x={px} y={groundY(px, "oars") - 6} width={38} height={12} rx={3} fill="#a8723c" stroke="#4a2c14" strokeWidth={2} transform={`rotate(${slope},${px},${groundY(px, "oars")})`} />;
          })}
          {/* rope to the pullers */}
          <line x1={x + 400 * Math.cos((slope * Math.PI) / 180) * 0.62} y1={gy - 150} x2={1100} y2={groundY(1100, "oars") - 75} stroke="#6b4a2a" strokeWidth={6} />
          {[820, 900, 980, 1060].map((px, i) => (
            <Puller key={px} x={px} y={groundY(px, "oars") - 2} t={t} i={i} />
          ))}
          <g transform={`translate(${x},${gy - 58}) rotate(${slope}) scale(0.88)`}>
            <SideGalley t={t} oarsInAir rollers={travel} />
          </g>
        </svg>
      </AbsoluteFill>
    );
  }

  // walk / outro: the galley strolls over a hill on little legs
  const isOutro = variant === "outro";
  const walkX = isOutro
    ? interpolate(local, [0, dur - 1.2], [-420, 1500], clamp)
    : interpolate(local, [0, dur], [-380, 560], { ...clamp, easing: Easing.out(Easing.quad) });
  const gy = groundY(walkX, variant);
  const slope = (Math.atan2(groundY(walkX + 10, variant) - groundY(walkX - 10, variant), 20) * 180) / Math.PI;
  const bob = Math.abs(Math.sin(t * 11)) * -14;
  return (
    <AbsoluteFill style={{ opacity }}>
      <Sky top={isOutro ? "#2a2550" : "#9fd3f0"} bottom={isOutro ? "#f2915a" : "#f2e6c4"} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        {isOutro && <circle cx={760} cy={880} r={140} fill="#ffd27a" opacity={0.9} />}
        {isOutro && <Skyline y={960} color="#3b2a40" opacity={0.85} />}
        {!isOutro && <rect x={0} y={990} width={1080} height={300} fill="#3f8ab3" />}
        <path d={`M-20,1920 L-20,${groundY(-20, variant)} ${Array.from({ length: 24 }, (_, i) => `L${i * 50},${groundY(i * 50, variant)}`).join(" ")} L1100,1920Z`} fill={isOutro ? "#8a6448" : "#c9a86b"} />
        <g transform={`translate(${walkX},${gy - 82 + bob}) rotate(${slope * 0.6 + Math.sin(t * 11) * 3}) scale(0.86)`}>
          <SideGalley t={t} legs />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
