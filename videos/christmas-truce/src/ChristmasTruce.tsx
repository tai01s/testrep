import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Battlefield, cameraAt } from "./Battlefield";
import { Captions } from "./Captions";
import { FrontMap } from "./FrontMap";
import { Overlays } from "./Overlays";
import { Soundtrack } from "./Soundtrack";
import { FPS, S, W } from "./timeline";

export const ChristmasTruce: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const cam = cameraAt(t);
  // the map of the front covers the first half of the setup line
  const mapA = S("setup") - 0.2, mapB = W("setup", "Between") - 0.1;
  const map = interpolate(t, [mapA, mapA + 0.4, mapB - 0.4, mapB], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#070b1c" }}>
      <Battlefield t={t} cam={cam} />
      {map > 0 && (
        <AbsoluteFill style={{ opacity: map }}>
          <FrontMap local={t - mapA} dur={mapB - mapA} />
        </AbsoluteFill>
      )}
      <Overlays t={t} cam={cam} />
      <Captions t={t} />
      <Soundtrack />
    </AbsoluteFill>
  );
};
