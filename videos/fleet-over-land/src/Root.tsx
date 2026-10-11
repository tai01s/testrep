import { Composition } from "remotion";
import { FleetOverLand } from "./FleetOverLand";
import { FPS, timelineFor } from "./timeline";

export const RemotionRoot = () => (
  <>
    {(["en", "tr"] as const).map((lang) => (
      <Composition
        key={lang}
        id={lang === "en" ? "FleetOverLand" : `FleetOverLand-${lang.toUpperCase()}`}
        component={FleetOverLand}
        defaultProps={{ lang }}
        durationInFrames={Math.ceil(timelineFor(lang).TOTAL * FPS)}
        fps={FPS}
        width={1080}
        height={1920}
      />
    ))}
  </>
);
