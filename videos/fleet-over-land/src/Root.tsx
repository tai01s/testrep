import { Composition } from "remotion";
import { FleetOverLand } from "./FleetOverLand";
import { FPS, TOTAL } from "./timeline";

export const RemotionRoot = () => (
  <Composition
    id="FleetOverLand"
    component={FleetOverLand}
    durationInFrames={Math.ceil(TOTAL * FPS)}
    fps={FPS}
    width={1080}
    height={1920}
  />
);
