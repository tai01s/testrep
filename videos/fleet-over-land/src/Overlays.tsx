import React from "react";
import { AbsoluteFill, Easing, interpolate } from "remotion";
import { E, S, TOTAL, W } from "./timeline";
import { fonts } from "./fonts";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ramp = (t: number, a: number, b: number, easing = Easing.bezier(0.33, 0, 0.2, 1)) => interpolate(t, [a, b], [0, 1], { ...clamp, easing });
/** visible between a and b with short fades */
const win = (t: number, a: number, b: number, f = 0.25) => ramp(t, a, a + f) * (1 - ramp(t, b - f, b));
const popIn = (t: number, a: number) => interpolate(t, [a, a + 0.35], [0.4, 1], { ...clamp, easing: Easing.out(Easing.back(2.2)) });

const Title: React.FC<{ children: React.ReactNode; size?: number; color?: string; style?: React.CSSProperties }> = ({ children, size = 96, color = "#fff", style }) => (
  <div
    style={{
      fontFamily: fonts.title, fontWeight: 900, fontSize: size, color, textAlign: "center", letterSpacing: size * 0.04, lineHeight: 1.05,
      textShadow: "0 6px 0 rgba(0,0,0,0.55), 0 0 30px rgba(0,0,0,0.6)", ...style,
    }}
  >
    {children}
  </div>
);

const Card: React.FC<{ children: React.ReactNode; opacity: number; scale?: number; top: number; bg?: string; border?: string }> = ({ children, opacity, scale = 1, top, bg = "rgba(20,14,8,0.82)", border = "#d8b24a" }) =>
  opacity <= 0.001 ? null : (
    <div style={{ position: "absolute", top, left: 0, right: 0, display: "flex", justifyContent: "center", opacity }}>
      <div style={{ transform: `scale(${scale})`, background: bg, border: `5px solid ${border}`, borderRadius: 28, padding: "26px 46px", boxShadow: "0 20px 50px rgba(0,0,0,0.45)" }}>
        {children}
      </div>
    </div>
  );

const Crescent: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100">
    <circle r={48} fill="#c62f24" stroke="#f3d27a" strokeWidth={4} />
    <circle r={30} fill="#fff" />
    <circle cx={10} r={25} fill="#c62f24" />
  </svg>
);

export const Overlays: React.FC<{ t: number }> = ({ t }) => {
  const els: React.ReactNode[] = [];

  // darkening + spotlight for the twist ("something nobody sees coming")
  const dark = win(t, S("twist") - 0.1, S("road") + 0.6, 0.6);
  if (dark > 0) {
    els.push(
      <AbsoluteFill key="dark" style={{ background: "radial-gradient(circle at 50% 42%, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 22%, rgba(5,8,20,0.82) 55%)", opacity: dark }} />
    );
    const q = popIn(t, S("twist") + 1.2);
    els.push(
      <div key="q" style={{ position: "absolute", top: 560, left: 0, right: 0, textAlign: "center", opacity: win(t, S("twist") + 1.2, S("road") + 0.3), transform: `scale(${q})` }}>
        <Title size={200} color="#ffe08a">?</Title>
      </div>
    );
  }

  // series chip
  const chip = win(t, S("setup") + 0.3, TOTAL - 2.2, 0.4) * (1 - win(t, S("oars"), E("oars"), 0.15));
  if (chip > 0)
    els.push(
      <div key="chip" style={{ position: "absolute", top: 210, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: chip }}>
        <div style={{ fontFamily: fonts.caption, fontWeight: 800, fontSize: 34, color: "#f6e7c1", background: "rgba(20,14,8,0.72)", padding: "12px 28px", borderRadius: 40, letterSpacing: 4, border: "3px solid rgba(216,178,74,0.8)" }}>
          SIEGE OF CONSTANTINOPLE · 1453
        </div>
      </div>
    );

  // hook title
  const hook = win(t, 0.15, E("hook1") + 0.05, 0.2);
  if (hook > 0)
    els.push(
      <div key="hook" style={{ position: "absolute", top: 300, left: 40, right: 40, opacity: hook, transform: `scale(${popIn(t, 0.15)})` }}>
        <Title size={92} color="#ffe08a">THE UNBREAKABLE</Title>
        <Title size={150}>CHAIN</Title>
      </div>
    );

  // Mehmed card
  const mehmed = win(t, W("setup", "Sultan") - 0.3, E("setup") + 0.1, 0.25);
  els.push(
    <Card key="mehmed" top={330} opacity={mehmed} scale={popIn(t, W("setup", "Sultan") - 0.3)} bg="rgba(120,20,14,0.9)">
      <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
        <Crescent size={130} />
        <div>
          <div style={{ fontFamily: fonts.title, fontWeight: 900, fontSize: 62, color: "#fff", letterSpacing: 3 }}>MEHMED II</div>
          <div style={{ fontFamily: fonts.caption, fontWeight: 800, fontSize: 40, color: "#f3d27a" }}>Ottoman Sultan · age 21</div>
        </div>
      </div>
    </Card>
  );

  // FAILED stamp
  const failAt = W("fail", "fails");
  const stamp = win(t, failAt - 0.05, E("fail") + 0.2, 0.15);
  if (stamp > 0) {
    const sc = interpolate(t, [failAt - 0.05, failAt + 0.12], [2.4, 1], { ...clamp, easing: Easing.in(Easing.quad) });
    els.push(
      <div key="stamp" style={{ position: "absolute", top: 420, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: stamp }}>
        <div style={{ transform: `rotate(-12deg) scale(${sc})`, border: "14px solid #e0261b", borderRadius: 24, padding: "10px 40px", background: "rgba(255,255,255,0.08)" }}>
          <div style={{ fontFamily: fonts.caption, fontWeight: 900, fontSize: 150, color: "#e0261b", letterSpacing: 10, textShadow: "0 4px 0 rgba(0,0,0,0.35)" }}>FAILED</div>
        </div>
      </div>
    );
  }

  // ship counter while they are dragged
  const cnt = win(t, S("drag") + 0.4, E("drag") + 0.1, 0.25);
  if (cnt > 0) {
    const n = Math.round(interpolate(t, [S("drag") + 0.5, W("drag", "70") + 0.6], [1, 70], { ...clamp, easing: Easing.out(Easing.quad) }));
    const beat = 1 + 0.06 * Math.max(0, Math.cos(((t - S("drag")) * Math.PI * 2) / 0.5)) ** 8;
    els.push(
      <div key="cnt" style={{ position: "absolute", top: 320, left: 0, right: 0, textAlign: "center", opacity: cnt, transform: `scale(${popIn(t, S("drag") + 0.4) * beat})` }}>
        <Title size={190} color="#ffe08a">×{n}</Title>
        <div style={{ fontFamily: fonts.caption, fontWeight: 900, fontSize: 52, color: "#fff", letterSpacing: 8, textShadow: "0 4px 12px rgba(0,0,0,0.8)" }}>SHIPS OVER THE HILL</div>
      </div>
    );
  }

  // date card: the morning of 22 April
  const apr = win(t, S("reveal") + 0.05, W("reveal", "enemy"), 0.25);
  els.push(
    <Card key="apr" top={330} opacity={apr} scale={popIn(t, S("reveal") + 0.05)}>
      <Title size={80} color="#ffe08a">22 APRIL 1453</Title>
      <div style={{ fontFamily: fonts.caption, fontWeight: 800, fontSize: 38, color: "#f6e7c1", textAlign: "center", marginTop: 8 }}>sunrise over the Golden Horn</div>
    </Card>
  );

  // defenders count
  const def = win(t, S("stretch") + 0.4, E("stretch") + 0.1, 0.3);
  els.push(
    <Card key="def" top={330} opacity={def} scale={popIn(t, S("stretch") + 0.4)} bg="rgba(16,26,60,0.86)" border="#8fa7ff">
      <div style={{ fontFamily: fonts.caption, fontWeight: 900, fontSize: 64, color: "#fff", textAlign: "center" }}>≈ 7,000 DEFENDERS</div>
      <div style={{ fontFamily: fonts.caption, fontWeight: 800, fontSize: 38, color: "#c9d4ff", textAlign: "center", marginTop: 6 }}>now spread across two fronts</div>
    </Card>
  );

  // the fall
  const fallAt = W("fall", "falls");
  const may = win(t, S("fall") + 0.1, E("fall") + 0.2, 0.3);
  els.push(
    <Card key="may" top={330} opacity={may} scale={popIn(t, S("fall") + 0.1)} bg="rgba(90,10,8,0.9)">
      <Title size={84} color="#fff">29 MAY 1453</Title>
      <div style={{ fontFamily: fonts.caption, fontWeight: 800, fontSize: 40, color: "#ffd9a8", textAlign: "center", marginTop: 8, opacity: ramp(t, W("fall", "empire") - 0.6, W("fall", "empire")) }}>
        Byzantine Empire · 330 – 1453
      </div>
    </Card>
  );
  const flash = interpolate(t, [fallAt - 0.05, fallAt + 0.05, fallAt + 0.6], [0, 0.85, 0], clamp);
  if (flash > 0) els.push(<AbsoluteFill key="flash" style={{ background: "#fff3dd", opacity: flash }} />);

  // end card
  const endT = E("outro") - 2.6;
  const end = ramp(t, endT, endT + 0.4);
  if (end > 0)
    els.push(
      <div key="end" style={{ position: "absolute", top: 330, left: 40, right: 40, opacity: end, transform: `scale(${popIn(t, endT)})` }}>
        <Title size={70} color="#ffe08a">THE FLEET THAT</Title>
        <Title size={104}>SAILED</Title>
        <Title size={104}>OVER LAND</Title>
        <div style={{ textAlign: "center", marginTop: 26, fontFamily: fonts.caption, fontWeight: 800, fontSize: 40, color: "#f6e7c1", opacity: ramp(t, endT + 0.8, endT + 1.2) }}>
          Constantinople · 22 April 1453
        </div>
      </div>
    );

  // vignette on top of everything
  els.push(<AbsoluteFill key="vig" style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)" }} />);
  return <>{els}</>;
};
