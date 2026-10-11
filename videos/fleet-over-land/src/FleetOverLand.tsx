import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { cameraAt } from "./camera";
import { Captions } from "./Captions";
import { Lang } from "./i18n";
import { MapLayer } from "./MapLayer";
import { Overlays } from "./Overlays";
import { SideScene } from "./SideScene";
import { Soundtrack } from "./Soundtrack";
import { FPS, TimelineContext, timelineFor } from "./timeline";

export const FleetOverLand: React.FC<{ lang: Lang }> = ({ lang }) => {
  const tl = timelineFor(lang);
  const { S, E } = tl;
  const t = useCurrentFrame() / FPS;
  const side = (id: string, variant: "walk" | "oars" | "outro") =>
    t >= S(id) && t < E(id) ? <SideScene variant={variant} local={t - S(id)} dur={E(id) - S(id)} t={t} /> : null;

  return (
    <TimelineContext.Provider value={tl}>
      {/* lang drives locale-aware text-transform (e.g. Turkish i -> İ) */}
      <AbsoluteFill lang={lang} style={{ background: "#123b52" }}>
        <MapLayer t={t} cam={cameraAt(t, tl)} />
        {side("hook2", "walk")}
        {side("oars", "oars")}
        {side("outro", "outro")}
        <Overlays t={t} />
        <Captions t={t} />
        <Soundtrack />
      </AbsoluteFill>
    </TimelineContext.Provider>
  );
};
