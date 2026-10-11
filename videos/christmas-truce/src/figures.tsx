import React from "react";

export type Side = "gb" | "de";

const COAT: Record<Side, string> = { gb: "#7a6b43", de: "#646b5e" };
const COAT_DARK: Record<Side, string> = { gb: "#5a4e30", de: "#4a5046" };
const SKIN = "#e0ae86";
const BOOT = "#2a2118";

export type Pose = {
  walk?: number; // walk-cycle phase in radians; undefined = standing
  armL?: number; // degrees from hanging straight down, positive = forward
  armR?: number;
  bow?: number; // 0..1 head bowed
  capOff?: boolean; // cap held in hand (mourning)
  kick?: number; // 0..1 front leg swing
};

/**
 * Side-view soldier, ~175 units tall, feet at the origin, facing +x
 * (pass facing=-1 to mirror). 1914 kit: British soft service cap,
 * German Pickelhaube.
 */
export const Soldier: React.FC<{ x: number; y: number; side: Side; facing?: 1 | -1; pose?: Pose; scale?: number; opacity?: number; tint?: string }> = ({
  x, y, side, facing = 1, pose = {}, scale = 1, opacity = 1, tint,
}) => {
  const swing = pose.walk !== undefined ? Math.sin(pose.walk) * 24 : 0;
  const legA = pose.kick !== undefined ? -10 - pose.kick * 55 : swing;
  const legB = pose.kick !== undefined ? 8 : -swing;
  const bob = pose.walk !== undefined ? Math.abs(Math.cos(pose.walk)) * -4 : 0;
  const armL = pose.armL ?? -swing * 0.8;
  const armR = pose.armR ?? swing * 0.8;
  const bow = (pose.bow ?? 0) * 28;
  const coat = tint ?? COAT[side];
  const leg = (deg: number, k: number) => (
    <g transform={`translate(${k * 4},-78) rotate(${-deg})`}>
      <path d="M-6,0 L6,0 L5,70 L-5,70Z" fill={COAT_DARK[side]} />
      <path d="M-6,62 L8,62 L16,78 L-6,78Z" fill={BOOT} />
    </g>
  );
  const arm = (deg: number, front: boolean, hand?: React.ReactNode) => (
    <g transform={`translate(${front ? 4 : -2},-140) rotate(${-deg})`}>
      <path d="M-6,0 L7,0 L5,62 L-5,62Z" fill={front ? coat : COAT_DARK[side]} />
      <circle cx={0} cy={66} r={6.5} fill={SKIN} />
      {hand}
    </g>
  );
  const cap =
    side === "gb" ? (
      <g>
        <path d="M-15,-6 Q0,-16 16,-7 L16,-1 L-15,-1Z" fill="#6b5d38" />
        <path d="M8,-2 L24,1 L8,2Z" fill="#3a3020" />
      </g>
    ) : (
      <g>
        <path d="M-14,0 Q-14,-20 0,-21 Q14,-20 14,0Z" fill="#3b3d36" />
        <path d="M11,-2 L24,2 L11,3Z" fill="#26271f" />
        <path d="M-15,1 L-21,3 L-14,4Z" fill="#26271f" />
        <path d="M-2,-21 L0,-36 L2,-21Z" fill="#8f8a74" />
      </g>
    );
  const capInHand = pose.capOff ? <g transform="translate(0,72) scale(0.9)">{cap}</g> : undefined;
  return (
    <g transform={`translate(${x},${y + bob * scale}) scale(${facing * scale},${scale})`} opacity={opacity}>
      {arm(armL, false)}
      {leg(legB, -1)}
      {leg(legA, 1)}
      {/* greatcoat */}
      <path d="M-16,-146 Q0,-152 16,-146 L24,-58 Q0,-52 -22,-58Z" fill={coat} />
      <path d="M-22,-58 Q0,-52 24,-58 L24,-66 Q0,-60 -22,-66Z" fill={COAT_DARK[side]} />
      <rect x={-19} y={-104} width={41} height={6} fill="#3a2e1c" />
      {/* head */}
      <g transform={`translate(2,-150) rotate(${bow})`}>
        <rect x={-6} y={-4} width={11} height={8} fill={SKIN} />
        <circle cx={1} cy={-14} r={13} fill={SKIN} />
        {side === "gb" && <path d="M7,-6 Q11,-4 13,-7" stroke="#5a3b22" strokeWidth={2.5} fill="none" />}
        {side === "de" && <path d="M6,-6 Q11,-3 15,-7 M6,-6 Q2,-3 -2,-6" stroke="#3a2b1c" strokeWidth={2.5} fill="none" />}
        {!pose.capOff && <g transform="translate(0,-18)">{cap}</g>}
        {pose.capOff && <path d="M-12,-20 Q1,-30 14,-20" stroke="#4a3522" strokeWidth={5} fill="none" />}
      </g>
      {arm(armR, true, capInHand)}
    </g>
  );
};

/** Small fir tree lit with candles, as the Germans put along their parapets. */
export const CandleTree: React.FC<{ x: number; y: number; t: number; lit: number; scale?: number; seed?: number }> = ({ x, y, t, lit, scale = 1, seed = 0 }) => {
  const candles: [number, number][] = [[-18, -18], [16, -22], [-10, -44], [12, -50], [-4, -70], [0, -92]];
  return (
    <g transform={`translate(${x},${y}) scale(${scale})`}>
      <rect x={-3} y={-8} width={6} height={10} fill="#4a3220" />
      <path d="M-30,-6 L0,-50 L30,-6Z M-24,-36 L0,-78 L24,-36Z M-17,-64 L0,-104 L17,-64Z" fill="#1f3a2a" stroke="#132619" strokeWidth={2} />
      {candles.map(([cx, cy], i) => {
        const on = Math.min(1, Math.max(0, lit * candles.length - i));
        if (on <= 0) return null;
        const flick = 0.75 + 0.25 * Math.sin(t * (9 + i) + seed * 3 + i * 2);
        return (
          <g key={i} opacity={on}>
            <circle cx={cx} cy={cy - 6} r={16 * flick} fill="url(#candleGlow)" />
            <rect x={cx - 1.6} y={cy - 6} width={3.2} height={7} fill="#f3ead2" />
            <ellipse cx={cx} cy={cy - 9} rx={2.2} ry={3.6 * flick} fill="#ffd36b" />
          </g>
        );
      })}
    </g>
  );
};

export const Note: React.FC<{ x: number; y: number; s?: number; color: string; opacity: number; double?: boolean }> = ({ x, y, s = 1, color, opacity, double }) => (
  <g transform={`translate(${x},${y}) scale(${s})`} opacity={opacity} fill={color}>
    {double ? (
      <>
        <ellipse cx={-10} cy={20} rx={9} ry={6.5} transform="rotate(-20,-10,20)" />
        <ellipse cx={18} cy={14} rx={9} ry={6.5} transform="rotate(-20,18,14)" />
        <rect x={-2.5} y={-22} width={4} height={42} />
        <rect x={25.5} y={-28} width={4} height={42} />
        <path d="M-2.5,-22 L29.5,-28 L29.5,-20 L-2.5,-14Z" />
      </>
    ) : (
      <>
        <ellipse cx={0} cy={20} rx={9} ry={6.5} transform="rotate(-20,0,20)" />
        <rect x={7} y={-22} width={4} height={42} />
        <path d="M11,-22 Q26,-10 20,4 Q22,-8 11,-12Z" />
      </>
    )}
  </g>
);

/** Things swapped in no man's land. */
export const Item: React.FC<{ kind: "cigarettes" | "chocolate" | "buttons" | "beer"; x: number; y: number; rot?: number; s?: number }> = ({ kind, x, y, rot = 0, s = 1 }) => (
  <g transform={`translate(${x},${y}) rotate(${rot}) scale(${s})`}>
    {kind === "cigarettes" && (
      <g>
        <rect x={-18} y={-12} width={36} height={24} rx={3} fill="#b8322a" stroke="#4a1410" strokeWidth={2} />
        <rect x={-18} y={-12} width={36} height={8} fill="#e8dcc0" />
        <rect x={-9} y={-24} width={5} height={14} fill="#f6f1e4" />
        <rect x={-2} y={-20} width={5} height={10} fill="#f6f1e4" />
        <rect x={-9} y={-25} width={5} height={3} fill="#d08a3a" />
      </g>
    )}
    {kind === "chocolate" && (
      <g>
        <rect x={-24} y={-13} width={48} height={26} rx={3} fill="#5b3418" stroke="#2c180a" strokeWidth={2} />
        {[-12, 0, 12].map((gx) => (
          <line key={gx} x1={gx} y1={-13} x2={gx} y2={13} stroke="#3c200e" strokeWidth={2} />
        ))}
        <line x1={-24} y1={0} x2={24} y2={0} stroke="#3c200e" strokeWidth={2} />
        <rect x={6} y={-13} width={18} height={26} fill="#2f5e8a" />
      </g>
    )}
    {kind === "buttons" && (
      <g>
        {[[-12, 0], [12, -4]].map(([bx, by], i) => (
          <g key={i} transform={`translate(${bx},${by})`}>
            <circle r={11} fill="#d6ad4f" stroke="#7a5a1c" strokeWidth={2} />
            <circle r={6} fill="none" stroke="#a37d2c" strokeWidth={1.5} />
            <circle cx={-2} cy={-2} r={2.5} fill="#fff3c4" opacity={0.7} />
          </g>
        ))}
      </g>
    )}
    {kind === "beer" && (
      <g>
        <path d="M-9,18 L-9,-6 Q-9,-12 -4,-15 L-4,-26 L4,-26 L4,-15 Q9,-12 9,-6 L9,18Z" fill="#6a3b12" stroke="#2c180a" strokeWidth={2} />
        <rect x={-9} y={-2} width={18} height={11} fill="#efe0b8" />
        <rect x={-5} y={-30} width={10} height={5} fill="#b9b9b9" />
      </g>
    )}
  </g>
);

export const Football: React.FC<{ x: number; y: number; rot: number }> = ({ x, y, rot }) => (
  <g transform={`translate(${x},${y}) rotate(${rot})`}>
    <circle r={13} fill="#8a5a2c" stroke="#3b2210" strokeWidth={2.5} />
    <path d="M-13,0 L13,0 M0,-13 Q6,0 0,13" stroke="#3b2210" strokeWidth={2} fill="none" />
  </g>
);
