# RainDash

A live Rain World stats dashboard for your TV (or any browser), styled like the game itself. It uses the game's own
karma symbols, creature icons, passage icons and bitmap font, which the mod extracts from your game install at runtime.

```
Rain World + RainDash mod  ──HTTP :8787──▶  Fire TV app (full-screen dashboard)
          │                                  └─ or any browser: http://<your-pc>:8787/
          └─ on launch: adb connect <firestick> → am start com.raindash.tv
```

## What it shows

| Tab | Contents |
| --- | --- |
| **Overview** | Cycle, sleeps, deaths, quits, kills, survival rate, food eaten, play time, karma, echoes, passages, regions visited, most-hunted creatures, how you died, kills this cycle, local creature reputation |
| **Kills** | Every creature you've killed with its in-game icon and colour, plus this cycle's kills (not saved until you sleep) |
| **Campaign** (named after your slugcat) | Campaign-specific live stats. **Artificer**: the hidden explosion counter (`pyroJumpCounter`) against the Remix "explosion capacity" (default 10, where you explode), its cooldown, lifetime explosive jumps, highest counter, self-explosions, scavenger kills and reputation. **Hunter**: cycles left before the illness. **Gourmand**: exhaustion and food quest. **Saint**: ascension power. **Rivulet**: rain timer, rarefaction cell. **Spearmaster**: needle regrowth, spears thrown. **Monk**: pacifism. Every campaign also gets vital signs (food, air, stun, stomach) and story progress (Moon/Pebbles state etc.) |
| **Passages** | Every passage with its icon and progress |
| **Map** | Pick any region. The whole region is drawn from the game's own room geometry, wiki-map style: subregions, connections, shelters, and karma gates showing the karma each side needs and where the gate leads. You're a pulsing dot. There's no GPS zoom; the whole region always fits the screen. Defaults to the region you're in. |
| **Lifetime** | Things RainDash counts itself and saves separately from the game: time in cycles, jumps, throws, spears, things eaten, rooms explored, causes of death, sleeps while starving, explosive jumps. These keep counting through deaths that roll your save back. |

The header always shows the slugcat, region, room, karma (with the karma-flower ring), the rain timer drawn as a
ring of pips around the karma symbol like the in-game HUD, and the food meter with its hibernation bar.

Remote controls: D-pad moves around, ⏪/⏩ switch tabs, Back returns to the tab bar (press again to exit), ☰ opens
the app's setup screen. The **Live campaign** button cycles through snapshots of other campaigns you've played.

## Install

### 1. The mod (PC)

Build it (needs the .NET SDK, plus the game installed, because it compiles against the game's DLLs):

```
cd mod
dotnet build -c Release -p:RainWorldDir="C:\Program Files (x86)\Steam\steamapps\common\Rain World"
```

Copy the `mod/raindash` folder (it now contains `plugins/RainDash.dll`) to
`Rain World\RainWorld_Data\StreamingAssets\mods\raindash`, start the game and enable **RainDash** in Remix.

The first time, Windows Firewall asks about Rain World. Allow it on **private networks**, or the TV can't connect.

### 2. The Fire TV app

Get the APK from this repo's **Actions → Build Fire TV APK** run (artifact `RainDash-FireTV`), or build it with
`gradle -p firetv assembleRelease` if you have the Android SDK.

On the Fire Stick: **Settings → My Fire TV → About**, click the device name 7 times to unlock Developer Options,
then **Developer Options → ADB debugging: ON** (and "Apps from unknown sources" if you'll use Downloader).

Install it from your PC with
[Android platform-tools](https://developer.android.com/tools/releases/platform-tools):

```
adb connect 192.168.1.50
adb install RainDash-FireTV.apk
```

Accept the "Allow USB debugging?" prompt on the TV (tick *Always allow from this computer*).

### 3. Auto-launch

In Rain World: **Options → Remix → RainDash**:

- **Auto-launch app on Fire Stick**: on by default. Every time Rain World starts, the mod runs
  `adb connect` and `am start` to open RainDash on the TV, pointed at your PC.
- **Fire Stick IP**: under Settings → My Fire TV → About → Network on the TV.
- **ADB path**: leave empty if `adb.exe` is on your PATH, in the mod folder (`raindash/platform-tools/adb.exe`) or in
  the Android SDK; otherwise give the full path.
- **Wake the TV**: sends a wake key first, which can switch the TV on over HDMI-CEC.
- **Launch on Fire Stick now**: test button that shows the result next to it.

Without ADB the app still works: open it from the Fire TV home screen and it finds the PC by itself (LAN
broadcast on UDP 47812), or type the address shown in the Remix menu.

## How it works

- `mod/src`: BepInEx plugin (C#, .NET 4.8).
  - `StatsCollector` reads the save state and live game state on the main thread four times a second and publishes a
    JSON snapshot. Version-sensitive fields such as `pyroJumpCounter`, `godTimer`, `totFood` and passage trackers
    are read by reflection, so a renamed field shows "—" instead of breaking the mod.
  - `Hooks` / `Tracker`: jumps, throws, eating, deaths (with cause), kills, sleeps and explosions, saved per save
    slot + campaign under `%USERPROFILE%\AppData\LocalLow\Videocult\Rain World\RainDash`.
  - `MapExporter` builds region maps from `world/xx/map_xx.txt` (layout), each room's `.txt` (terrain),
    `world_xx.txt` (shelters/gates) and `world/gates/locks.txt` (gate karma). Modded regions work too.
  - `AssetExporter` renders sprites and the `DisplayFont` bitmap font out of Futile's atlases into PNGs
    (cached), so nothing from the game is redistributed.
  - `HttpServer` is a tiny GET-only server on `0.0.0.0:8787` serving `raindash/www` and the `/api/*` endpoints.
    `DiscoveryResponder` answers the TV app's LAN broadcast.
  - `FireStickLauncher` runs the ADB connect/launch sequence on a background thread.
- `mod/raindash/www`: the dashboard (plain HTML/CSS/JS, no build step).
- `firetv`: the Android TV/Fire TV app, a full-screen WebView with a setup screen, LAN discovery, offline/retry
  screen, and remote-key handling.
- `tools/mock-server.js`: serves the dashboard with fake data for UI work:
  `node tools/mock-server.js 8787 Artificer`, then open http://localhost:8787.

## API

| Endpoint | |
| --- | --- |
| `GET /api/state` | live snapshot (`status`, `campaign`, `live`, `tracker`) |
| `GET /api/regions?slug=` | regions that have a map |
| `GET /api/map/{REGION}?slug=` | rooms (position, size, terrain, shelter/gate/lock), connections, subregions |
| `GET /api/campaigns`, `/api/campaign/{key}` | cached snapshots of other campaigns |
| `GET /icon/{sprite}`, `/icon/karma/{0-9}[/big]` | game sprites as PNG |
| `GET /font/DisplayFont.json|.png` | the game's bitmap font |

## Caveats

- The mod was written against Rain World 1.9.x (Downpour) without being able to run the game, so expect a first
  round of fixes. Anything read by reflection degrades to "—" rather than crashing. Check `BepInEx/LogOutput.log`
  for lines starting with `RainDash` / `[FireStick]`.
- Map scale: the map files don't say how many map units a tile is, so the dashboard picks the largest scale at
  which rooms on the same layer don't overlap.
- Gate karma comes straight from `locks.txt` (left number = left door, right = right door).
