using System;
using System.Reflection;
using MonoMod.RuntimeDetour;

namespace RainDash
{
    /// <summary>Game hooks that feed the <see cref="Tracker"/>.</summary>
    public static class Hooks
    {
        static bool pyroDying;

        public static void Apply()
        {
            On.Player.Jump += Player_Jump;
            On.Player.ThrowObject += Player_ThrowObject;
            On.Player.ObjectEaten += Player_ObjectEaten;
            On.Player.Die += Player_Die;
            On.Creature.Die += Creature_Die;

            // These signatures differ between game versions / DLCs, so hook them by reflection.
            HookByReflection(typeof(Player), "PyroDeath", nameof(PyroDeath0));
            HookByReflection(typeof(RainWorldGame), "Win", nameof(Win1), nameof(Win2));
        }

        static Tracker T(Creature c)
        {
            if (c == null || c.room == null) return null;
            return StatsCollector.CurrentTracker(c.room.game);
        }

        static void Player_Jump(On.Player.orig_Jump orig, Player self)
        {
            orig(self);
            try
            {
                var t = T(self);
                if (t != null) t.Add("jumps");
            }
            catch (Exception e) { Plugin.Log.LogError(e); }
        }

        static void Player_ThrowObject(On.Player.orig_ThrowObject orig, Player self, int grasp, bool eu)
        {
            try
            {
                var t = T(self);
                var obj = self.grasps != null && grasp >= 0 && grasp < self.grasps.Length && self.grasps[grasp] != null
                    ? self.grasps[grasp].grabbed
                    : null;
                if (t != null && obj != null)
                {
                    string type = obj.abstractPhysicalObject.type.value;
                    t.Add("throws");
                    t.AddTo("thrown", type);
                    if (obj is Spear) t.Add("spearsThrown");
                }
            }
            catch (Exception e) { Plugin.Log.LogError(e); }
            orig(self, grasp, eu);
        }

        static void Player_ObjectEaten(On.Player.orig_ObjectEaten orig, Player self, IPlayerEdible edible)
        {
            try
            {
                var t = T(self);
                if (t != null && edible != null)
                {
                    string type = "Unknown";
                    if (edible is Creature cr) type = cr.Template.type.value;
                    else if (edible is PhysicalObject po) type = po.abstractPhysicalObject.type.value;
                    t.Add("itemsEaten");
                    t.AddTo("eaten", type);
                }
            }
            catch (Exception e) { Plugin.Log.LogError(e); }
            orig(self, edible);
        }

        static void Player_Die(On.Player.orig_Die orig, Player self)
        {
            try
            {
                if (!self.dead)
                {
                    var t = T(self);
                    if (t != null)
                    {
                        string cause = DeathCause(self);
                        t.Add("deaths");
                        t.AddTo("deathCauses", cause);
                        if (Refl.Has(self, "pyroJumpCounter"))
                            t.Max("pyroCounterAtDeath", Refl.Get(self, "pyroJumpCounter", 0));
                        Tracker.SaveAll();
                    }
                }
            }
            catch (Exception e) { Plugin.Log.LogError(e); }
            orig(self);
        }

        static void Creature_Die(On.Creature.orig_Die orig, Creature self)
        {
            try
            {
                if (!self.dead && !(self is Player) && self.killTag != null &&
                    self.killTag.creatureTemplate.type == CreatureTemplate.Type.Slugcat)
                {
                    var t = T(self);
                    if (t != null)
                    {
                        t.Add("kills");
                        t.AddTo("killsByType", self.Template.type.value);
                    }
                }
            }
            catch (Exception e) { Plugin.Log.LogError(e); }
            orig(self);
        }

        public static string DeathCause(Player p)
        {
            try
            {
                if (pyroDying) return "Explosion";

                if (p.grabbedBy != null)
                    foreach (var g in p.grabbedBy)
                        if (g != null && g.grabber != null && !(g.grabber is Player))
                            return g.grabber.Template.type.value;

                if (p.room != null && p.mainBodyChunk != null && p.mainBodyChunk.pos.y < 0f)
                    return "Fell";

                var rain = p.room != null ? Refl.Get(p.room.world, "rainCycle") : null;
                if (rain != null && Refl.Get(rain, "TimeUntilRain", 1) <= 0) return "Rain";

                if (Refl.Get(p, "airInLungs", 1f) <= 0.05f) return "Drowned";

                if (p.killTag != null && p.killTag.creatureTemplate != null)
                    return p.killTag.creatureTemplate.type.value;

                if (Refl.Get(p, "Malnourished", false)) return "Starved";
            }
            catch (Exception) { }
            return "Unknown";
        }

        // ------------------------------------------------------------------ reflection hooks

        public delegate void OrigPyroDeath(Player self);
        public delegate void OrigWin1(RainWorldGame self, bool malnourished);
        public delegate void OrigWin2(RainWorldGame self, bool malnourished, bool fromWarpPoint);

        static void PyroDeath0(OrigPyroDeath orig, Player self)
        {
            var t = T(self);
            if (t != null) t.Add("explosionDeaths");
            pyroDying = true;
            try { orig(self); }
            finally { pyroDying = false; }
        }

        static void Win1(OrigWin1 orig, RainWorldGame self, bool malnourished)
        {
            OnWin(self, malnourished);
            orig(self, malnourished);
            AfterWin();
        }

        static void Win2(OrigWin2 orig, RainWorldGame self, bool malnourished, bool fromWarpPoint)
        {
            OnWin(self, malnourished);
            orig(self, malnourished, fromWarpPoint);
            AfterWin();
        }

        static void OnWin(RainWorldGame game, bool malnourished)
        {
            try
            {
                var t = StatsCollector.CurrentTracker(game);
                if (t == null) return;
                t.Add("sleeps");
                if (malnourished) t.Add("starvingSleeps");
            }
            catch (Exception e) { Plugin.Log.LogError(e); }
        }

        static void AfterWin()
        {
            try
            {
                Tracker.SaveAll();
                StatsCollector.FlushCampaign();
            }
            catch (Exception e) { Plugin.Log.LogError(e); }
        }

        /// <summary>
        /// Hooks <paramref name="type"/>.<paramref name="method"/> with whichever of our handlers has the matching
        /// number of parameters (handler params = orig + self + method params).
        /// </summary>
        static void HookByReflection(Type type, string method, params string[] handlers)
        {
            try
            {
                foreach (var target in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                {
                    if (target.Name != method || target.DeclaringType != type) continue;
                    int n = target.GetParameters().Length;
                    foreach (var h in handlers)
                    {
                        var handler = typeof(Hooks).GetMethod(h, BindingFlags.NonPublic | BindingFlags.Static);
                        if (handler == null || handler.GetParameters().Length != n + 2) continue;
                        new Hook(target, handler);
                        Plugin.Log.LogInfo("Hooked " + type.Name + "." + method + " (" + n + " params)");
                        return;
                    }
                }
                Plugin.Log.LogInfo("Not hooking " + type.Name + "." + method + " (not present in this game version)");
            }
            catch (Exception e)
            {
                Plugin.Log.LogWarning("Could not hook " + type.Name + "." + method + ": " + e.Message);
            }
        }
    }
}
