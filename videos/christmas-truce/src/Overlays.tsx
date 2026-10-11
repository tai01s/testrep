import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, random, staticFile } from "remotion";
import { Cam } from "./Battlefield";
import { Note } from "./figures";
import { fonts } from "./fonts";
import { E, S, TOTAL, W } from "./timeline";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ramp = (t: number, a: number, b: number, easing = Easing.bezier(0.33, 0, 0.2, 1)) => interpolate(t, [a, b], [0, 1], { ...clamp, easing });
const win = (t: number, a: number, b: number, f = 0.3) => ramp(t, a, a + f) * (1 - ramp(t, b - f, b));
const pop = (t: number, a: number) => interpolate(t, [a, a + 0.45], [0.85, 1], { ...clamp, easing: Easing.out(Easing.back(1.8)) });

const toScreen = (x: number, y: number, cam: Cam) => [(x - cam.cx) * cam.z + 540, (y - cam.cy) * cam.z + 960];

const Title: React.FC<{ children: React.ReactNode; size: number; color?: string; spacing?: number; style?: React.CSSProperties }> = ({ children, size, color = "#f4efe4", spacing = 0.08, style }) => (
  <div style={{ fontFamily: fonts.title, fontWeight: 900, fontSize: size, color, letterSpacing: size * spacing, textAlign: "center", lineHeight: 1.08, textShadow: "0 4px 24px rgba(0,0,0,0.75)", ...style }}>
    {children}
  </div>
);

const Small: React.FC<{ children: React.ReactNode; color?: string; size?: number }> = ({ children, color = "#d9d2c2", size = 34 }) => (
  <div style={{ fontFamily: fonts.caption, fontWeight: 800, fontSize: size, color, letterSpacing: 6, textAlign: "center", textShadow: "0 3px 12px rgba(0,0,0,0.8)" }}>{children}</div>
);

const At: React.FC<{ top: number; opacity: number; scale?: number; children: React.ReactNode }> = ({ top, opacity, scale = 1, children }) =>
  opacity <= 0.001 ? null : (
    <div style={{ position: "absolute", top, left: 40, right: 40, opacity, transform: `scale(${scale})` }}>{children}</div>
  );

const Snow: React.FC<{ t: number; amount: number }> = ({ t, amount }) => {
  if (amount <= 0) return null;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: amount }}>
      {Array.from({ length: 140 }, (_, i) => {
        const depth = 0.4 + random(`d${i}`) * 0.9;
        const speed = 60 + depth * 90;
        const y = ((random(`y${i}`) * 2100 + t * speed) % 2100) - 90;
        const x = (random(`x${i}`) * 1180 + Math.sin(t * 0.6 + i) * 30 * depth + t * 12 * depth) % 1180 - 50;
        return <circle key={i} cx={x} cy={y} r={2 + depth * 3.5} fill="#fff" opacity={0.35 + depth * 0.45} />;
      })}
    </svg>
  );
};

export const Overlays: React.FC<{ t: number; cam: Cam }> = ({ t, cam }) => {
  const els: React.ReactNode[] = [];
  const nobodyAt = S("nobody");

  // hook title
  els.push(
    <At key="hook" top={330} opacity={win(t, 0.8, E("hook") - 0.2, 0.5)} scale={pop(t, 0.8)}>
      <Small color="#e7b25c">THE WESTERN FRONT</Small>
      <Title size={104} style={{ marginTop: 14 }}>24 DECEMBER</Title>
      <Title size={150} color="#e7b25c">1914</Title>
    </At>
  );

  // cross-section labels
  const xs = win(t, W("setup", "Between") + 0.2, E("setup") + 0.2, 0.35);
  if (xs > 0) {
    const [gx, gy] = toScreen(770, 1110, cam);
    const [dx] = toScreen(2430, 1110, cam);
    const [ax] = toScreen(1030, 0, cam);
    const [bx] = toScreen(2170, 0, cam);
    const [, ny] = toScreen(0, 990, cam);
    els.push(
      <div key="xs" style={{ position: "absolute", inset: 0, opacity: xs }}>
        <div style={{ position: "absolute", left: gx - 100, top: gy - 210, width: 200 }}><Small color="#e6d9a8" size={30}>BRITISH</Small></div>
        <div style={{ position: "absolute", left: dx - 100, top: gy - 210, width: 200 }}><Small color="#c9cdc2" size={30}>GERMAN</Small></div>
        <div style={{ position: "absolute", left: ax, top: ny - 90, width: bx - ax }}>
          <Small color="#fff" size={38}>NO MAN'S LAND</Small>
          <svg width={bx - ax} height={40} style={{ display: "block", marginTop: 8 }}>
            <path d={`M6,20 L${bx - ax - 6},20 M6,20 l16,-10 m-16,10 l16,10 M${bx - ax - 6},20 l-16,-10 m16,10 l-16,10`} stroke="#fff" strokeWidth={4} fill="none" />
          </svg>
          <div style={{ marginTop: 6, opacity: ramp(t, W("setup", "less") - 0.2, W("setup", "less") + 0.3) }}>
            <Small color="#e7b25c" size={44}>&lt; 100 M</Small>
          </div>
        </div>
      </div>
    );
  }

  // place card: near Ypres
  els.push(
    <At key="ypres" top={300} opacity={win(t, W("trees", "Ypres") - 0.2, E("trees"), 0.4)} scale={pop(t, W("trees", "Ypres") - 0.2)}>
      <Small color="#e7b25c">CHRISTMAS EVE</Small>
      <Title size={76} style={{ marginTop: 10 }}>NEAR YPRES</Title>
      <Small size={30}>BELGIUM</Small>
    </At>
  );

  // carols
  const lyric = (key: string, a: number, b: number, line: string, lang: string, color: string) =>
    els.push(
      <At key={key} top={320} opacity={win(t, a, b, 0.4)} scale={pop(t, a)}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 22 }}>
          <svg width={60} height={70} viewBox="-20 -35 60 70"><Note x={0} y={0} color={color} opacity={1} s={1.1} /></svg>
          <div>
            <div style={{ fontFamily: fonts.title, fontWeight: 700, fontSize: 60, color, fontStyle: "italic", textAlign: "center", textShadow: "0 3px 16px rgba(0,0,0,0.8)" }}>{line}</div>
            <Small size={26}>{lang}</Small>
          </div>
          <svg width={60} height={70} viewBox="-20 -35 60 70"><Note x={0} y={0} color={color} opacity={1} s={1.1} double /></svg>
        </div>
      </At>
    );
  lyric("stille", W("sing", "Stille") - 0.3, E("sing"), "Stille Nacht, heilige Nacht", "GERMAN TRENCHES", "#ffe6a6");
  lyric("faithful", W("answer", "carols") - 0.2, W("answer", "Song") + 0.2, "O Come, All Ye Faithful", "BRITISH TRENCHES", "#bfe3ff");

  // Christmas morning
  els.push(
    <At key="xmas" top={320} opacity={win(t, S("morning") + 0.2, E("morning") - 0.1, 0.4)} scale={pop(t, S("morning") + 0.2)}>
      <Small color="#9b2d22">CHRISTMAS DAY</Small>
      <Title size={96} color="#2b2a2a" style={{ textShadow: "0 2px 14px rgba(255,255,255,0.5)" }}>25 DECEMBER</Title>
    </At>
  );

  // NOBODY SHOOTS.
  const nb = win(t, nobodyAt - 0.05, E("nobody") - 0.1, 0.25);
  if (nb > 0)
    els.push(
      <AbsoluteFill key="nobody" style={{ justifyContent: "center", alignItems: "center", opacity: nb }}>
        <div style={{ transform: `scale(${interpolate(t, [nobodyAt, E("nobody")], [1, 1.08], clamp)})`, marginTop: -260 }}>
          <Title size={128} color="#1f1d1c" spacing={0.06} style={{ textShadow: "0 0 40px rgba(255,255,255,0.7)" }}>NOBODY</Title>
          <Title size={128} color="#1f1d1c" spacing={0.06} style={{ textShadow: "0 0 40px rgba(255,255,255,0.7)" }}>SHOOTS.</Title>
        </div>
      </AbsoluteFill>
    );

  // calendar: how long it lasted
  const cal = win(t, S("lasts") + 0.1, E("lasts") + 0.2, 0.35);
  if (cal > 0) {
    const page = t < W("lasts", "Boxing") - 0.1 ? 0 : t < W("lasts", "new") - 0.1 ? 1 : 2;
    const pages = [["25", "DECEMBER", "Christmas Day"], ["26", "DECEMBER", "Boxing Day"], ["1", "JANUARY", "1915"]][page];
    const flipAt = [S("lasts"), W("lasts", "Boxing") - 0.1, W("lasts", "new") - 0.1][page];
    const flip = interpolate(t, [flipAt, flipAt + 0.3], [90, 0], { ...clamp, easing: Easing.out(Easing.quad) });
    els.push(
      <div key="cal" style={{ position: "absolute", top: 300, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: cal, perspective: 900 }}>
        <div style={{ width: 360, background: "#f6f1e6", borderRadius: 18, boxShadow: "0 24px 60px rgba(0,0,0,0.5)", overflow: "hidden", transform: `rotateX(${flip}deg)`, transformOrigin: "top" }}>
          <div style={{ background: "#9b2d22", color: "#fff", fontFamily: fonts.caption, fontWeight: 900, fontSize: 38, letterSpacing: 6, textAlign: "center", padding: "14px 0" }}>{pages[1]}</div>
          <div style={{ fontFamily: fonts.title, fontWeight: 900, fontSize: 190, color: "#262321", textAlign: "center", lineHeight: 1.1 }}>{pages[0]}</div>
          <div style={{ fontFamily: fonts.caption, fontWeight: 800, fontSize: 34, color: "#6b6258", textAlign: "center", paddingBottom: 22 }}>{pages[2]}</div>
        </div>
      </div>
    );
  }

  // orders from above
  const ord = win(t, S("orders") + 0.1, E("orders") + 0.1, 0.35);
  if (ord > 0) {
    const stampAt = W("orders", "never") - 0.1;
    const st = interpolate(t, [stampAt, stampAt + 0.14], [2.2, 1], { ...clamp, easing: Easing.in(Easing.quad) });
    els.push(
      <div key="orders" style={{ position: "absolute", top: 260, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: ord }}>
        <div style={{ width: 640, background: "#ece3cf", padding: "40px 46px", boxShadow: "0 24px 60px rgba(0,0,0,0.55)", transform: "rotate(-2deg)", position: "relative" }}>
          <div style={{ fontFamily: fonts.title, fontWeight: 900, fontSize: 44, color: "#2a2520", letterSpacing: 4 }}>HIGH COMMAND</div>
          <div style={{ fontFamily: fonts.caption, fontWeight: 700, fontSize: 24, color: "#6b6258", letterSpacing: 3, marginTop: 4 }}>ORDERS TO ALL UNITS</div>
          {[0.92, 0.8, 0.87, 0.6, 0.83, 0.7].map((w, i) => (
            <div key={i} style={{ height: 12, width: `${w * 100}%`, background: "#b9ad96", borderRadius: 6, marginTop: i === 0 ? 30 : 16 }} />
          ))}
          {t >= stampAt && (
            <div style={{ position: "absolute", right: 30, bottom: 30, transform: `rotate(-14deg) scale(${st})`, border: "8px solid #b3261e", borderRadius: 14, padding: "6px 18px",
              fontFamily: fonts.caption, fontWeight: 900, fontSize: 52, color: "#b3261e", letterSpacing: 4, opacity: 0.92 }}>
              NO MORE TRUCES
            </div>
          )}
        </div>
      </div>
    );
  }

  // the war goes on
  const war = win(t, S("war") + 0.1, E("war") + 0.1, 0.35);
  if (war > 0) {
    const yr = Math.min(1918, 1915 + Math.floor(ramp(t, S("war") + 0.6, W("war", "claims"), Easing.linear) * 3.999));
    els.push(
      <At key="war" top={320} opacity={war} scale={pop(t, S("war") + 0.1)}>
        <Small color="#e06a5a">THE WAR GOES ON</Small>
        <Title size={190} color="#f4efe4">{yr}</Title>
      </At>
    );
  }

  // closing title + channel logo
  const endT = S("outro") + 0.4;
  const end = ramp(t, endT, endT + 0.8);
  if (end > 0)
    els.push(
      <At key="end" top={280} opacity={end} scale={pop(t, endT)}>
        <Small color="#e7b25c">CHRISTMAS 1914</Small>
        <Title size={92} style={{ marginTop: 12 }}>THE</Title>
        <Title size={124}>CHRISTMAS</Title>
        <Title size={124}>TRUCE</Title>
      </At>
    );
  const logo = ramp(t, TOTAL - 3.0, TOTAL - 2.3);
  if (logo > 0)
    els.push(
      <div key="logo" style={{ position: "absolute", left: 0, right: 0, top: 1420, display: "flex", justifyContent: "center", opacity: logo }}>
        <Img src={staticFile("logo.png")} style={{ width: 520 }} />
      </div>
    );

  return (
    <>
      <Snow t={t} amount={ramp(t, W("hook", "nobody") - 0.5, W("hook", "nobody") + 2) * (1 - 0.6 * win(t, S("war"), E("war"), 0.5))} />
      {els}
      {/* vignette + grain for an archival feel */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 50%, rgba(0,0,0,0.55) 100%)" }} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: 0.13, mixBlendMode: "overlay" }}>
        <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={Math.floor(t * 24) % 50} /><feColorMatrix type="saturate" values="0" /></filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </>
  );
};
