import { Composition } from "remotion";
import { ChristmasTruce } from "./ChristmasTruce";
import { FPS, TOTAL } from "./timeline";

export const RemotionRoot = () => (
  <Composition id="ChristmasTruce" component={ChristmasTruce} durationInFrames={Math.ceil(TOTAL * FPS)} fps={FPS} width={1080} height={1920} />
);
