using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace RainDash
{
    /// <summary>
    /// Builds region maps for the dashboard straight from the game's world files
    /// (World/XX/map_XX.txt for layout, the room .txt files for terrain, World/Gates/locks.txt for karma gates),
    /// so modded and Downpour regions work too. File-only, safe to run on the HTTP threads.
    /// </summary>
    public static class MapExporter
    {
        static readonly Dictionary<string, string> cache = new Dictionary<string, string>();
        static readonly Dictionary<string, string> nameCache = new Dictionary<string, string>();

        static string Resolve(string relative)
        {
            try
            {
                string p = AssetManager.ResolveFilePath(relative);
                if (!string.IsNullOrEmpty(p) && File.Exists(p)) return p;
            }
            catch (Exception) { }
            return null;
        }

        static string ResolveFor(string dir, string file, string ext, string slug)
        {
            if (!string.IsNullOrEmpty(slug))
            {
                string p = Resolve(dir + "/" + file + "-" + slug.ToLowerInvariant() + ext);
                if (p != null) return p;
            }
            return Resolve(dir + "/" + file + ext);
        }

        public static string RegionName(string acronym, string slug)
        {
            string key = acronym + "|" + slug;
            lock (nameCache)
            {
                if (nameCache.TryGetValue(key, out var n)) return n;
            }
            string name = null;
            try
            {
                var slugName = slug != null ? new SlugcatStats.Name(slug, false) : null;
                name = Refl.CallStatic("Region", "GetRegionFullName", acronym, slugName) as string;
            }
            catch (Exception) { }
            if (string.IsNullOrEmpty(name)) name = acronym;
            lock (nameCache) nameCache[key] = name;
            return name;
        }

        public static string RegionListJson(string slug)
        {
            var list = new List<object>();
            var seen = new HashSet<string>();
            string regions = Resolve("World/regions.txt");
            if (regions != null)
            {
                foreach (var raw in File.ReadAllLines(regions))
                {
                    string r = raw.Trim();
                    if (r.Length == 0 || !seen.Add(r.ToUpperInvariant())) continue;
                    if (ResolveFor("World/" + r, "map_" + r, ".txt", slug) == null) continue;
                    list.Add(new Dictionary<string, object> { { "id", r.ToUpperInvariant() }, { "name", RegionName(r, slug) } });
                }
            }
            return Json.Serialize(list);
        }

        public static string RegionJson(string region, string slug)
        {
            region = region.ToUpperInvariant();
            foreach (char c in region)
                if (!char.IsLetterOrDigit(c) && c != '_') return null;
            string key = region + "|" + slug;
            lock (cache)
            {
                if (cache.TryGetValue(key, out var cached)) return cached;
            }
            string json = Build(region, slug);
            if (json != null)
                lock (cache) cache[key] = json;
            return json;
        }

        static string Build(string region, string slug)
        {
            string mapFile = ResolveFor("World/" + region, "map_" + region, ".txt", slug);
            if (mapFile == null) return null;

            var worldRooms = ParseWorldFile(region, slug);
            var subregions = ParseSubregions(region, slug);
            var locks = ParseLocks();

            var rooms = new List<object>();
            var connections = new List<object>();
            var placed = new HashSet<string>();

            foreach (var raw in File.ReadAllLines(mapFile))
            {
                string line = raw.Trim();
                if (line.Length == 0) continue;
                int colon = line.IndexOf(':');
                if (colon <= 0) continue;
                string head = line.Substring(0, colon).Trim();
                string rest = line.Substring(colon + 1).Trim();

                if (head == "Connection")
                {
                    var parts = rest.Split(',');
                    if (parts.Length < 6) continue;
                    connections.Add(new List<object>
                    {
                        parts[0].Trim(), parts[1].Trim(),
                        Num(parts[2]), Num(parts[3]), Num(parts[4]), Num(parts[5]),
                    });
                    continue;
                }

                string roomName = head.ToUpperInvariant();
                if (worldRooms != null && worldRooms.Count > 0 && !worldRooms.ContainsKey(roomName)) continue;
                if (!placed.Add(roomName)) continue;

                var f = Regex.Split(rest, "><");
                if (f.Length < 2) continue;
                var room = new Dictionary<string, object>
                {
                    { "name", roomName },
                    { "x", Num(f[0]) },
                    { "y", Num(f[1]) },
                    { "layer", f.Length > 4 ? (int)Num(f[4]) : 0 },
                };
                string sub = f.Length > 5 ? f[5].Trim() : "";
                if (int.TryParse(sub, out int subIndex))
                    sub = subIndex > 0 && subIndex <= subregions.Count ? subregions[subIndex - 1] : "";
                room["sub"] = sub;

                string tags = null;
                if (worldRooms != null && worldRooms.TryGetValue(roomName, out tags))
                {
                    room["shelter"] = tags.Contains("SHELTER");
                    room["ancientShelter"] = tags.Contains("ANCIENTSHELTER");
                    room["scav"] = tags.Contains("SCAVOUTPOST") || tags.Contains("SCAVTRADER");
                    room["swarm"] = tags.Contains("SWARMROOM");
                }
                bool gate = roomName.StartsWith("GATE_") || (tags != null && tags.Contains("GATE"));
                room["gate"] = gate;
                if (gate && locks.TryGetValue(roomName, out var lockInfo)) room["lock"] = lockInfo;

                AddGeometry(room, roomName, region);
                rooms.Add(room);
            }

            var result = new Dictionary<string, object>
            {
                { "id", region },
                { "name", RegionName(region, slug) },
                { "slugcat", slug },
                { "subregions", subregions.ConvertAll(s => (object)s) },
                { "rooms", rooms },
                { "connections", connections },
            };
            return Json.Serialize(result);
        }

        static double Num(string s)
        {
            double d;
            return double.TryParse(s.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out d) ? d : 0;
        }

        /// <summary>ROOMS section of world_XX.txt: room name → tags (SHELTER, GATE, ...).</summary>
        static Dictionary<string, string> ParseWorldFile(string region, string slug)
        {
            string file = ResolveFor("World/" + region, "world_" + region, ".txt", slug);
            if (file == null) return null;
            var rooms = new Dictionary<string, string>();
            bool inRooms = false;
            foreach (var raw in File.ReadAllLines(file))
            {
                string line = raw.Trim();
                if (line == "ROOMS") { inRooms = true; continue; }
                if (line == "END ROOMS") { inRooms = false; continue; }
                if (!inRooms || line.Length == 0 || line.StartsWith("//")) continue;

                // Slugcat-conditional rooms look like "(White,Yellow)SU_A01 : ..." or "{Spear}SU_A01 : ...".
                if (line[0] == '(' || line[0] == '{')
                {
                    char close = line[0] == '(' ? ')' : '}';
                    int end = line.IndexOf(close);
                    if (end < 0) continue;
                    string cond = line.Substring(1, end - 1);
                    line = line.Substring(end + 1).Trim();
                    if (!ConditionMatches(cond, slug)) continue;
                }

                var parts = line.Split(':');
                string name = parts[0].Trim().ToUpperInvariant();
                if (name.Length == 0) continue;
                var tags = new StringBuilder();
                for (int i = 2; i < parts.Length; i++) tags.Append(parts[i].Trim().ToUpperInvariant()).Append(' ');
                rooms[name] = tags.ToString();
            }
            return rooms;
        }

        static bool ConditionMatches(string cond, string slug)
        {
            if (string.IsNullOrEmpty(slug)) return true;
            bool exclude = cond.StartsWith("X-");
            if (exclude) cond = cond.Substring(2);
            bool listed = false;
            foreach (var s in cond.Split(','))
                if (string.Equals(s.Trim(), slug, StringComparison.OrdinalIgnoreCase)) listed = true;
            return exclude ? !listed : listed;
        }

        static List<string> ParseSubregions(string region, string slug)
        {
            var list = new List<string>();
            string file = ResolveFor("World/" + region, "properties", ".txt", slug);
            if (file == null) return list;
            foreach (var raw in File.ReadAllLines(file))
            {
                string line = raw.Trim();
                if (line.StartsWith("Subregion:")) list.Add(line.Substring("Subregion:".Length).Trim());
            }
            return list;
        }

        /// <summary>World/Gates/locks.txt: "GATE_SU_HI : 2 : 1" → karma needed from the left / right side.</summary>
        static Dictionary<string, object> ParseLocks()
        {
            var locks = new Dictionary<string, object>();
            string file = Resolve("World/Gates/locks.txt");
            if (file == null) return locks;
            foreach (var raw in File.ReadAllLines(file))
            {
                var parts = raw.Split(':');
                if (parts.Length < 3) continue;
                locks[parts[0].Trim().ToUpperInvariant()] = new Dictionary<string, object>
                {
                    { "left", parts[1].Trim() },
                    { "right", parts[2].Trim() },
                    { "swap", raw.Contains("SWAPMAPSYMBOL") },
                };
            }
            return locks;
        }

        static string FindRoomFile(string room, string region)
        {
            try
            {
                var p = Refl.CallStatic("WorldLoader", "FindRoomFile", room, false, ".txt") as string;
                if (!string.IsNullOrEmpty(p) && File.Exists(p)) return p;
            }
            catch (Exception) { }
            string prefix = room.Split('_')[0];
            foreach (var candidate in new[]
                     {
                         "World/" + region + "-Rooms/" + room + ".txt",
                         "World/" + prefix + "-Rooms/" + room + ".txt",
                         "World/Gates/" + room + ".txt",
                         "World/Gate Shelters/" + room + ".txt",
                     })
            {
                string p = Resolve(candidate);
                if (p != null) return p;
            }
            return null;
        }

        /// <summary>
        /// Adds w/h (tiles), water level and a terrain string: one char per tile, row by row from the top.
        /// '0' air, '1' solid, '2' slope, '3' platform, '4' shortcut entrance.
        /// </summary>
        static void AddGeometry(Dictionary<string, object> room, string roomName, string region)
        {
            string file = FindRoomFile(roomName, region);
            if (file == null) return;
            string[] lines;
            try { lines = File.ReadAllLines(file); }
            catch (Exception) { return; }
            if (lines.Length < 2) return;

            var sizeParts = lines[1].Split('|');
            var wh = sizeParts[0].Split('*');
            if (wh.Length < 2 || !int.TryParse(wh[0], out int w) || !int.TryParse(wh[1], out int h)) return;
            room["w"] = w;
            room["h"] = h;
            if (sizeParts.Length > 1 && int.TryParse(sizeParts[1], out int water)) room["water"] = water;

            // The geometry line is normally lines[11]; search for it in case of odd files.
            string geo = null;
            if (lines.Length > 11 && lines[11].Split('|').Length >= w * h) geo = lines[11];
            else
                foreach (var l in lines)
                    if (l.Length > w * h && l.Split('|').Length >= w * h) { geo = l; break; }
            if (geo == null) return;

            // Stored column by column (x outer), each column from top to bottom.
            var cells = geo.Split('|');
            var grid = new char[w * h];
            for (int i = 0; i < grid.Length; i++) grid[i] = '0';
            int idx = 0;
            for (int x = 0; x < w; x++)
            {
                for (int yTop = 0; yTop < h; yTop++, idx++)
                {
                    if (idx >= cells.Length) break;
                    string cell = cells[idx];
                    char t = cell.Length > 0 ? cell[0] : '0';
                    if (t < '0' || t > '4') t = '0';
                    grid[yTop * w + x] = t;
                }
            }
            room["tiles"] = new string(grid);
        }
    }
}
