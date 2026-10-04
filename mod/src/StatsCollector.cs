using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace RainDash
{
    /// <summary>
    /// Reads game state on the main thread and publishes it as a JSON snapshot the HTTP threads can serve.
    /// </summary>
    public static class StatsCollector
    {
        /// <summary>Latest /api/state payload. Swapped atomically; never mutated after publishing.</summary>
        public static volatile string StateJson = "{\"status\":\"starting\"}";

        static float publishTimer, campaignTimer, saveTimer;
        static Dictionary<string, object> lastCampaign;
        static Dictionary<string, object> lastTracker;
        static string lastCampaignKey;
        static string prevRoom;
        static int prevPyro = -1;
        static bool loggedError;

        public static RainWorld RW
        {
            get { return RWCustom.Custom.rainWorld; }
        }

        public static RainWorldGame CurrentGame()
        {
            var rw = RW;
            if (rw == null || rw.processManager == null) return null;
            return rw.processManager.currentMainLoop as RainWorldGame;
        }

        public static Tracker CurrentTracker(RainWorldGame game)
        {
            if (game == null || !game.IsStorySession) return null;
            var save = game.GetStorySession.saveState;
            if (save == null) return null;
            return Tracker.For(RW.options.saveSlot, save.saveStateNumber.value);
        }

        public static Player FirstPlayer(RainWorldGame game)
        {
            if (game == null || game.Players == null) return null;
            foreach (var ac in game.Players)
                if (ac != null && ac.realizedCreature is Player p) return p;
            return null;
        }

        public static void Tick(float dt)
        {
            var game = CurrentGame();
            try
            {
                if (game != null && game.IsStorySession) TickGame(game, dt);
                else
                {
                    prevRoom = null;
                    prevPyro = -1;
                }
            }
            catch (Exception e)
            {
                LogOnce(e);
            }

            saveTimer += dt;
            if (saveTimer > 30f)
            {
                saveTimer = 0f;
                Tracker.SaveAll();
            }

            publishTimer += dt;
            campaignTimer += dt;
            if (publishTimer < 0.25f) return;
            publishTimer = 0f;
            try
            {
                StateJson = Json.Serialize(BuildState(game));
            }
            catch (Exception e)
            {
                LogOnce(e);
            }
        }

        static void LogOnce(Exception e)
        {
            if (loggedError) return;
            loggedError = true;
            Plugin.Log.LogError("RainDash stats error (further errors suppressed): " + e);
        }

        // ------------------------------------------------------------------ per-frame tracking

        static void TickGame(RainWorldGame game, float dt)
        {
            var tracker = CurrentTracker(game);
            if (tracker == null) return;
            if (!Refl.Get(game, "GamePaused", false)) tracker.Add("timePlayed", dt);

            var player = FirstPlayer(game);
            if (player == null) return;

            var room = player.abstractCreature.Room;
            if (room != null && room.name != prevRoom)
            {
                prevRoom = room.name;
                tracker.VisitRoom(room.name);
                tracker.Add("roomTransitions");
            }

            int pyro = Refl.Get(player, "pyroJumpCounter", -1);
            if (pyro >= 0)
            {
                if (prevPyro >= 0 && pyro > prevPyro) tracker.Add("pyroJumps", pyro - prevPyro);
                tracker.Max("pyroMaxCounter", pyro);
                prevPyro = pyro;
            }
        }

        // ------------------------------------------------------------------ snapshot

        static Dictionary<string, object> BuildState(RainWorldGame game)
        {
            var state = new Dictionary<string, object>
            {
                { "mod", Plugin.Version },
                { "time", (DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalMilliseconds },
                { "url", Plugin.DashboardUrl() },
            };

            if (game == null || !game.IsStorySession)
            {
                state["status"] = game == null ? "menu" : "arena";
                state["campaign"] = lastCampaign;
                state["tracker"] = lastTracker;
                state["live"] = null;
                return state;
            }

            var session = game.GetStorySession;
            var save = session.saveState;
            string slug = save.saveStateNumber.value;
            int slot = RW.options.saveSlot;
            string key = Tracker.KeyFor(slot, slug);

            if (lastCampaign == null || campaignTimer > 2f || key != lastCampaignKey)
            {
                campaignTimer = 0f;
                lastCampaign = Campaign(save, slot, slug, key);
                if (key != lastCampaignKey || UnityEngine.Random.value < 0.1f)
                    Tracker.SaveCampaignCache(key, Json.Serialize(lastCampaign));
                lastCampaignKey = key;
            }

            var tracker = CurrentTracker(game);
            lastTracker = tracker != null ? tracker.ToJson() : null;

            state["status"] = "ingame";
            state["campaign"] = lastCampaign;
            state["tracker"] = lastTracker;
            state["live"] = Live(game, session, save, slug);
            return state;
        }

        /// <summary>Forces the campaign cache to be written (called when a cycle ends).</summary>
        public static void FlushCampaign()
        {
            var game = CurrentGame();
            if (game == null || !game.IsStorySession) return;
            var save = game.GetStorySession.saveState;
            string slug = save.saveStateNumber.value;
            int slot = RW.options.saveSlot;
            string key = Tracker.KeyFor(slot, slug);
            lastCampaign = Campaign(save, slot, slug, key);
            lastCampaignKey = key;
            Tracker.SaveCampaignCache(key, Json.Serialize(lastCampaign));
        }

        static Dictionary<string, object> Campaign(SaveState save, int slot, string slug, string key)
        {
            var dp = save.deathPersistentSaveData;
            var c = new Dictionary<string, object>
            {
                { "key", key },
                { "slot", slot },
                { "slugcat", slug },
                { "color", SlugcatColor(save.saveStateNumber) },
                { "cycle", save.cycleNumber },
                { "karma", dp.karma },
                { "karmaCap", dp.karmaCap },
                { "reinforced", dp.reinforcedKarma },
                { "deaths", dp.deaths },
                { "survives", dp.survives },
                { "quits", dp.quits },
                { "food", save.food },
                { "totFood", Refl.Get(save, "totFood", -1) },
                { "totTime", Refl.Get(save, "totTime", -1) },
                { "theMark", Refl.Get(dp, "theMark", false) },
                { "theGlow", Refl.Get(save, "theGlow", false) },
                { "shelter", Refl.Get<object>(save, "denPosition", null) },
                { "kills", Kills(Refl.Get(save, "kills")) },
                { "echoes", Echoes(Refl.Get(dp, "ghostsTalkedTo")) },
                { "passages", Passages(Refl.Get(dp, "winState")) },
                { "regionsVisited", RegionsVisited(slug) },
                { "extras", Extras(save, dp) },
                { "updated", (DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalMilliseconds },
            };
            return c;
        }

        public static string SlugcatColor(SlugcatStats.Name name)
        {
            try { return Hex(PlayerGraphics.DefaultSlugcatColor(name)); }
            catch (Exception) { return "#ffffff"; }
        }

        public static string Hex(Color c)
        {
            return "#" + ColorUtility.ToHtmlStringRGB(c).ToLowerInvariant();
        }

        static List<object> Kills(object killList)
        {
            var result = new List<object>();
            if (!(killList is IEnumerable list)) return result;
            foreach (var entry in list)
            {
                if (entry == null) continue;
                var data = Refl.Get(entry, "Key");
                int count = Refl.Get(entry, "Value", 0);
                var k = IconInfo(data);
                k["count"] = count;
                result.Add(k);
            }
            return result;
        }

        static List<object> SessionKills(StoryGameSession session)
        {
            var result = new List<object>();
            var records = Refl.Get(session, "playerSessionRecords") as IEnumerable;
            if (records == null) return result;
            var counts = new Dictionary<string, Dictionary<string, object>>();
            foreach (var rec in records)
            {
                var kills = Refl.Get(rec, "kills") as IEnumerable;
                if (kills == null) continue;
                foreach (var kill in kills)
                {
                    var info = IconInfo(Refl.Get(kill, "symbolData"));
                    string id = info["type"] + ":" + info["intData"];
                    Dictionary<string, object> existing;
                    if (counts.TryGetValue(id, out existing)) existing["count"] = (int)existing["count"] + 1;
                    else
                    {
                        info["count"] = 1;
                        counts[id] = info;
                        result.Add(info);
                    }
                }
            }
            return result;
        }

        /// <summary>Creature type + icon sprite + icon colour for an IconSymbol.IconSymbolData.</summary>
        public static Dictionary<string, object> IconInfo(object data)
        {
            var info = new Dictionary<string, object>();
            var crit = Refl.Get(data, "critType");
            info["type"] = crit != null ? crit.ToString() : "Unknown";
            info["intData"] = Refl.Get(data, "intData", 0);
            string sprite = Refl.CallStatic("CreatureSymbol", "SpriteNameOfCreature", data) as string;
            info["sprite"] = sprite ?? "Futile_White";
            var col = Refl.CallStatic("CreatureSymbol", "ColorOfCreature", data);
            info["color"] = col is Color c ? Hex(c) : "#ffffff";
            if (sprite != null) AssetExporter.Request(sprite);
            return info;
        }

        static List<object> Echoes(object ghosts)
        {
            var result = new List<object>();
            if (!(ghosts is IDictionary dict)) return result;
            foreach (DictionaryEntry e in dict)
                result.Add(new Dictionary<string, object> { { "id", e.Key.ToString() }, { "value", Refl.Convert(e.Value, 0) } });
            return result;
        }

        static List<object> Passages(object winState)
        {
            var result = new List<object>();
            if (!(Refl.Get(winState, "endgameTrackers") is IEnumerable trackers)) return result;
            foreach (var t in trackers)
            {
                if (t == null) continue;
                var idObj = Refl.Get(t, "ID");
                string id = idObj != null ? idObj.ToString() : "?";
                var p = new Dictionary<string, object>
                {
                    { "id", id },
                    { "name", Refl.CallStatic("WinState", "PassageDisplayName", idObj) as string ?? id },
                    { "sprite", id + "A" },
                    { "done", Refl.Get(t, "GoalAlreadyFullfilled", false) || Refl.Get(t, "GoalFullfilled", false) },
                    { "kind", t.GetType().Name },
                };
                double progress = 0, max = 0;
                var prog = Refl.Get(t, "progress");
                if (prog is bool[] bools)
                {
                    max = bools.Length;
                    foreach (var b in bools) if (b) progress++;
                }
                else if (prog is int[] ints)
                {
                    max = ints.Length;
                    foreach (var i in ints) if (i > 0) progress++;
                }
                else if (prog != null)
                {
                    progress = Refl.Convert(prog, 0.0);
                    max = Refl.Get(t, "max", 0.0);
                }
                else if (Refl.Get(t, "myList") is ICollection myList)
                {
                    progress = myList.Count;
                    max = Refl.Get(t, "totItemsToWin", 0.0);
                }
                p["progress"] = progress;
                p["max"] = max;
                AssetExporter.Request(id + "A");
                result.Add(p);
            }
            return result;
        }

        static List<object> RegionsVisited(string slug)
        {
            var result = new List<object>();
            var misc = Refl.Get(Refl.Get(RW.progression, "miscProgressionData"), "regionsVisited") as IDictionary;
            if (misc == null) return result;
            foreach (DictionaryEntry e in misc)
            {
                if (e.Value is IEnumerable slugs)
                    foreach (var s in slugs)
                        if (s != null && s.ToString() == slug)
                        {
                            result.Add(e.Key.ToString());
                            break;
                        }
            }
            return result;
        }

        static readonly string[] dpExtras =
        {
            "redsDeath", "redsExtraCycles", "ascended", "altEnding", "pebblesHasIncreasedRedsCycles",
            "foodReplenishBonus", "friendsSaved", "chatlogsRead", "sawVoidBathSlideshow",
        };

        static readonly string[] miscExtras =
        {
            "moonRevived", "pebblesSeenGreenNeuron", "pebblesEnergyTaken", "moonHeartRestored", "smPearlTagged",
            "halcyonStolen", "SSaiConversationsHad", "SSaiThrowOuts", "pebblesRivuletPostgame", "energySeenState",
            "hasRobo", "cyclesSinceSSai",
        };

        static readonly string[] oracleExtras =
        {
            "neuronsLeft", "totNeuronsGiven", "playerEncounters", "totalItemsBrought", "neuronGiveConversationCounter",
        };

        static Dictionary<string, object> Extras(SaveState save, DeathPersistentSaveData dp)
        {
            var x = new Dictionary<string, object>();
            CopyPrimitives(dp, dpExtras, x, "");
            var misc = Refl.Get(save, "miscWorldSaveData");
            CopyPrimitives(misc, miscExtras, x, "");
            CopyPrimitives(Refl.Get(misc, "SLOracleState"), oracleExtras, x, "moon_");

            // Hunter's cycle limit (19 cycles, +5 if Pebbles extended it).
            int extra = Refl.Get(dp, "redsExtraCycles", 0);
            var limit = Refl.CallStatic("RedsIllness", "RedsCycles", extra > 0);
            if (limit != null) x["redsCycleLimit"] = Refl.Convert(limit, 0);
            return x;
        }

        static void CopyPrimitives(object src, string[] names, Dictionary<string, object> into, string prefix)
        {
            if (src == null) return;
            foreach (var n in names)
            {
                if (!Refl.Has(src, n)) continue;
                var v = Refl.Get(src, n);
                if (v == null) continue;
                if (v is bool || v is int || v is float || v is double || v is string) into[prefix + n] = v;
                else if (v is IConvertible) into[prefix + n] = v.ToString();
            }
        }

        static Dictionary<string, object> Live(RainWorldGame game, StoryGameSession session, SaveState save, string slug)
        {
            var live = new Dictionary<string, object>();
            var world = game.world;
            string region = world != null ? world.name : null;
            live["region"] = region;
            live["regionName"] = region != null ? MapExporter.RegionName(region, slug) : null;

            var rain = world != null ? Refl.Get(world, "rainCycle") : null;
            if (rain != null)
            {
                live["rain"] = new Dictionary<string, object>
                {
                    { "timeUntilRain", Refl.Get(rain, "TimeUntilRain", 0) },
                    { "cycleLength", Refl.Get(rain, "cycleLength", 0) },
                    { "timer", Refl.Get(rain, "timer", 0) },
                    { "preTimer", Refl.Get(rain, "preTimer", 0) },
                    { "maxPreTimer", Refl.Get(rain, "maxPreTimer", 0) },
                    { "amountLeft", Refl.Get(rain, "AmountLeft", 0f) },
                };
            }

            var players = new List<object>();
            int index = 0;
            foreach (var ac in game.Players)
            {
                if (ac == null) continue;
                players.Add(PlayerInfo(ac, index++, slug));
            }
            live["players"] = players;
            live["cycleKills"] = SessionKills(session);
            live["reputation"] = Reputation(game);
            live["paused"] = Refl.Get(game, "GamePaused", false);
            return live;
        }

        static Dictionary<string, object> PlayerInfo(AbstractCreature ac, int index, string slug)
        {
            var info = new Dictionary<string, object> { { "index", index } };
            var room = ac.Room;
            info["room"] = room != null ? room.name : null;
            info["x"] = ac.pos.x;
            info["y"] = ac.pos.y;
            info["inShortcut"] = Refl.Get(ac.realizedCreature, "inShortcut", false);

            var p = ac.realizedCreature as Player;
            if (p == null)
            {
                info["realized"] = false;
                return info;
            }
            info["realized"] = true;
            if (p.room != null && p.mainBodyChunk != null)
            {
                info["x"] = p.mainBodyChunk.pos.x / 20f;
                info["y"] = p.mainBodyChunk.pos.y / 20f;
            }
            info["dead"] = p.dead;
            info["food"] = Refl.Get(p, "FoodInStomach", 0);
            info["quarterFood"] = Refl.Get(Refl.Get(p, "playerState"), "quarterFoodPoints", 0);
            var stats = Refl.Get(p, "slugcatStats");
            info["maxFood"] = Refl.Get(stats, "maxFood", 7);
            info["foodToHibernate"] = Refl.Get(stats, "foodToHibernate", 4);
            info["malnourished"] = Refl.Get(p, "Malnourished", false);
            info["airInLungs"] = Refl.Get(p, "airInLungs", 1f);
            info["stun"] = Refl.Get(p, "stun", 0);
            info["glowing"] = Refl.Get(p, "glowing", false);
            info["special"] = Special(p, slug);
            return info;
        }

        static Dictionary<string, object> Special(Player p, string slug)
        {
            var s = new Dictionary<string, object>();

            // Artificer: every explosive jump/parry raises pyroJumpCounter; it cools back down over time.
            // Reaching the Remix "explosion capacity" (default 10) kills you.
            if (Refl.Has(p, "pyroJumpCounter"))
            {
                int cap = Refl.ConfigValue(Refl.GetStatic("MoreSlugcats.MoreSlugcats", "cfgArtificerExplosionCapacity"), 10);
                s["pyroCounter"] = Refl.Get(p, "pyroJumpCounter", 0);
                s["pyroCapacity"] = cap;
                s["pyroCooldown"] = Refl.Get(p, "pyroJumpCooldown", 0f);
                s["pyroParryCooldown"] = Refl.Get(p, "pyroParryCooldown", 0f);
                s["pyroDropLock"] = Refl.Get(p, "pyroJumpDropLock", 0);
            }

            // Gourmand exhaustion.
            if (Refl.Has(p, "gourmandExhausted"))
            {
                s["gourmandExhausted"] = Refl.Get(p, "gourmandExhausted", false);
                s["aerobicLevel"] = Refl.Get(p, "aerobicLevel", 0f);
                s["lungsExhausted"] = Refl.Get(p, "lungsExhausted", false);
            }

            // Saint ascension.
            if (Refl.Has(p, "godTimer"))
            {
                s["godTimer"] = Refl.Get(p, "godTimer", 0f);
                s["maxGodTime"] = Refl.Get(p, "maxGodTime", 0f);
                s["monkAscension"] = Refl.Get(p, "monkAscension", false);
                s["godDeactiveTimer"] = Refl.Get(p, "godDeactiveTimer", 0f);
            }

            // Spearmaster needles.
            var spearOnBack = Refl.Get(p, "spearOnBack");
            if (spearOnBack != null) s["spearOnBackHas"] = Refl.Get(spearOnBack, "HasASpear", false);
            if (Refl.Has(p, "tailSpecks")) s["needleProgress"] = Refl.Get(Refl.Get(p, "tailSpecks"), "spearProg", 0f);

            s["adrenaline"] = Refl.Get(p, "Adrenaline", 0f);
            s["exhausted"] = Refl.Get(p, "exhausted", false);
            s["swallowed"] = Refl.Get(Refl.Get(p, "objectInStomach"), "type") is object o ? o.ToString() : null;
            return s;
        }

        static Dictionary<string, object> Reputation(RainWorldGame game)
        {
            var rep = new Dictionary<string, object>();
            var communities = Refl.Get(game.session, "creatureCommunities");
            if (communities == null || game.world == null || game.world.region == null) return rep;
            int region = Refl.Get(game.world.region, "regionNumber", 0);
            foreach (var name in new[] { "Scavengers", "Lizards", "Cicadas", "GarbageWorms", "Deer", "Jetfish" })
            {
                var id = Refl.GetStatic("CreatureCommunities+CommunityID", name);
                if (id == null) continue;
                var like = CallInstance(communities, "LikeOfPlayer", id, region, 0);
                if (like != null) rep[name] = Refl.Convert(like, 0f);
            }
            return rep;
        }

        static object CallInstance(object obj, string method, params object[] args)
        {
            try
            {
                foreach (var m in obj.GetType().GetMethods())
                    if (m.Name == method && m.GetParameters().Length == args.Length) return m.Invoke(obj, args);
            }
            catch (Exception) { }
            return null;
        }
    }
}
