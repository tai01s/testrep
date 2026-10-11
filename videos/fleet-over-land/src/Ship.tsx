import React from "react";

export const OTTOMAN = { hull: "#6b3d1c", trim: "#c62f24", sail: "#f4ead2", flag: "#d7261e" };
export const BYZANTINE = { hull: "#3a2b4f", trim: "#d8b24a", sail: "#efe6cf", flag: "#7b3fa0" };

type Colors = typeof OTTOMAN;

/** Top-down galley for the map, ~26 world units long, bow pointing along `angle`. */
export const Ship: React.FC<{
  x: number;
  y: number;
  angle: number;
  t: number;
  colors?: Colors;
  scale?: number;
  wake?: number; // 0..1 strength of the wake (moving in water)
  rollers?: boolean; // on land: show logs underneath
  rowing?: boolean;
  opacity?: number;
}> = ({ x, y, angle, t, colors = OTTOMAN, scale = 1, wake = 0, rollers = false, rowing = true, opacity = 1 }) => {
  const stroke = rowing ? Math.sin(t * 7 + x * 0.1) * 0.6 : 0;
  return (
    <g transform={`translate(${x},${y}) rotate(${angle}) scale(${scale})`} opacity={opacity}>
      {wake > 0 && (
        <path d="M-12,0 L-40,-9 M-12,0 L-40,9" stroke="#e8f6ff" strokeWidth={1.6} opacity={0.55 * wake} strokeLinecap="round" fill="none" />
      )}
      {rollers &&
        [-9, -3, 3, 9].map((rx) => (
          <rect key={rx} x={rx - 1.1} y={-6.5} width={2.2} height={13} rx={1} fill="#8b5a2b" stroke="#3b2210" strokeWidth={0.4} />
        ))}
      {/* oars */}
      {[-7, -3.5, 0, 3.5, 7].map((ox) => (
        <g key={ox}>
          <line x1={ox} y1={-3} x2={ox - 2 + stroke * 2} y2={-8} stroke="#3b2210" strokeWidth={0.7} />
          <line x1={ox} y1={3} x2={ox - 2 + stroke * 2} y2={8} stroke="#3b2210" strokeWidth={0.7} />
        </g>
      ))}
      <path d="M-12,-3 Q0,-4.6 9,-2.4 L14,0 L9,2.4 Q0,4.6 -12,3 Q-13.5,0 -12,-3Z" fill={colors.hull} stroke="#22140a" strokeWidth={0.6} />
      <line x1={-10} y1={0} x2={8} y2={0} stroke={colors.trim} strokeWidth={1.1} />
      {/* lateen yard + sail seen from above */}
      <path d="M-7,-5.5 Q2,-1 9,5" stroke={colors.sail} strokeWidth={2.4} fill="none" strokeLinecap="round" />
      <circle cx={1} cy={0} r={1} fill="#22140a" />
      <path d="M-12,-0.2 L-17,-2.5 L-16,-0.2Z" fill={colors.flag} />
    </g>
  );
};

/** Big side-view galley. Origin at keel middle, bow to the right, ~760px long. */
export const SideGalley: React.FC<{
  t: number;
  legs?: boolean; // cartoon walking legs
  oarsInAir?: boolean;
  rollers?: number; // distance travelled, spins the rollers
  colors?: Colors;
}> = ({ t, legs = false, oarsInAir = false, rollers, colors = OTTOMAN }) => {
  const oarPhase = Math.sin(t * 5.2);
  const billow = Math.sin(t * 2.1) * 6;
  return (
    <g>
      {rollers !== undefined &&
        [-260, -130, 0, 130, 260].map((rx) => {
          // rollers stay on the ground while the hull slides over them
          const travel = ((rollers + rx + 400) % 650) - 325;
          return (
            <g key={rx} transform={`translate(${travel},42) rotate(${(rollers / 24) * 57.3})`}>
              <circle r={24} fill="#9a6532" stroke="#3b2210" strokeWidth={4} />
              <circle r={15} fill="none" stroke="#6e4422" strokeWidth={2} />
              <line x1={-24} y1={0} x2={24} y2={0} stroke="#3b2210" strokeWidth={3} />
              {/* grease sheen */}
              <path d="M-16,-16 A22,22 0 0 1 10,-21" stroke="#fff4c4" strokeWidth={4} fill="none" opacity={0.7} />
            </g>
          );
        })}
      {legs &&
        [-200, -40, 120, 260].map((lx, i) => {
          const ph = t * 11 + i * Math.PI * 0.5;
          const a = Math.sin(ph) * 30, b = Math.sin(ph + Math.PI) * 30;
          const leg = (sw: number, k: number) => (
            <g key={k} transform={`translate(${lx + k * 22},6) rotate(${sw})`}>
              <path d="M0,0 L0,80 Q0,94 18,94 L34,94" stroke="#2a1a0e" strokeWidth={15} fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          );
          return (
            <g key={lx}>
              {leg(a, 0)}
              {leg(b, 1)}
            </g>
          );
        })}
      {/* oars */}
      {[-240, -180, -120, -60, 0, 60, 120, 180, 240].map((ox, i) => {
        const ang = legs ? 165 + oarPhase * 10 : oarsInAir ? 174 + oarPhase * 12 : 112 + oarPhase * 14;
        return (
          <g key={ox} transform={`translate(${ox},-12) rotate(${ang - 90 + (i % 2) * 0})`}>
            <line x1={0} y1={0} x2={0} y2={210} stroke="#4a2c14" strokeWidth={7} strokeLinecap="round" />
            <rect x={-8} y={180} width={16} height={46} rx={6} fill="#5a3518" />
          </g>
        );
      })}
      {/* hull */}
      <path
        d="M-335,-48 L345,-48 Q355,-20 330,-6 L410,-14 L336,8 Q300,34 220,38 L-250,38 Q-320,30 -335,-48Z"
        fill={colors.hull}
        stroke="#1f1208"
        strokeWidth={5}
      />
      <path d="M-335,-48 Q-372,-90 -350,-150 Q-338,-160 -330,-148 Q-346,-100 -318,-56Z" fill={colors.hull} stroke="#1f1208" strokeWidth={5} />
      <rect x={-322} y={-40} width={660} height={13} fill={colors.trim} />
      <rect x={-322} y={-27} width={660} height={4} fill="#e2b84b" />
      {[-240, -180, -120, -60, 0, 60, 120, 180, 240].map((ox) => (
        <circle key={ox} cx={ox} cy={-12} r={6} fill="#1f1208" />
      ))}
      {/* crew */}
      {[-260, -150, -40, 70, 180, 280].map((cx, i) => (
        <g key={cx} transform={`translate(${cx},${-62 + Math.sin(t * 5.2 + i) * 2})`}>
          <rect x={-9} y={-6} width={18} height={20} rx={4} fill="#8a2a1f" />
          <circle cy={-16} r={10} fill="#c98f63" />
          <ellipse cy={-25} rx={12} ry={8} fill="#f3eee2" />
        </g>
      ))}
      {/* mast, yard, sail */}
      <rect x={-26} y={-470} width={12} height={425} fill="#4a2c14" />
      <clipPath id="sailClip">
        <path d={`M-250,-150 L230,-500 L${20 + billow},-60 Z`} />
      </clipPath>
      <path d={`M-250,-150 L230,-500 L${20 + billow},-60 Z`} fill={colors.sail} stroke="#bfae8a" strokeWidth={4} />
      <path clipPath="url(#sailClip)" d={`M-160,-215 L${30 + billow * 0.8},-120 M-70,-280 L${40 + billow * 0.6},-185 M20,-345 L${55 + billow * 0.4},-250 M110,-410 L${70 + billow * 0.2},-320`} stroke={colors.trim} strokeWidth={16} opacity={0.9} />
      <line x1={-262} y1={-142} x2={242} y2={-508} stroke="#3b2210" strokeWidth={9} strokeLinecap="round" />
      <path d={`M-14,-470 Q30,${-478 + billow} 70,-466 Q40,-456 -14,-452Z`} fill={colors.flag} />
    </g>
  );
};
