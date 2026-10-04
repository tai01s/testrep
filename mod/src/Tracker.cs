using System;
using System.Collections.Generic;
using System.IO;

namespace RainDash
{
    /// <summary>
    /// Stats Rain World itself doesn't save (jumps, throws, causes of death, explosions...). Stored per
    /// save slot + campaign in persistentDataPath/RainDash. These are "lifetime" numbers: they keep counting
    /// even when a death rolls your save back.
    /// </summary>
    public class Tracker
    {
        public string Key;
        public readonly Dictionary<string, double> Counters = new Dictionary<string, double>();
        public readonly Dictionary<string, Dictionary<string, double>> Maps = new Dictionary<string, Dictionary<string, double>>();
        public readonly HashSet<string> RoomsVisited = new HashSet<string>();
        public bool Dirty;

        public void Add(string counter, double amount = 1)
        {
            double v;
            Counters.TryGetValue(counter, out v);
            Counters[counter] = v + amount;
            Dirty = true;
        }

        public void Max(string counter, double value)
        {
            double v;
            if (!Counters.TryGetValue(counter, out v) || value > v)
            {
                Counters[counter] = value;
                Dirty = true;
            }
        }

        public double Get(string counter)
        {
            double v;
            Counters.TryGetValue(counter, out v);
            return v;
        }

        public void AddTo(string map, string key, double amount = 1)
        {
            Dictionary<string, double> m;
            if (!Maps.TryGetValue(map, out m)) Maps[map] = m = new Dictionary<string, double>();
            double v;
            m.TryGetValue(key, out v);
            m[key] = v + amount;
            Dirty = true;
        }

        public void VisitRoom(string room)
        {
            if (RoomsVisited.Add(room)) Dirty = true;
        }

        public Dictionary<string, object> ToJson()
        {
            var counters = new Dictionary<string, object>();
            foreach (var kv in Counters) counters[kv.Key] = kv.Value;
            var maps = new Dictionary<string, object>();
            foreach (var kv in Maps)
            {
                var m = new Dictionary<string, object>();
                foreach (var e in kv.Value) m[e.Key] = e.Value;
                maps[kv.Key] = m;
            }
            var rooms = new List<object>();
            foreach (var r in RoomsVisited) rooms.Add(r);
            return new Dictionary<string, object>
            {
                { "key", Key },
                { "counters", counters },
                { "maps", maps },
                { "roomsVisited", rooms },
            };
        }

        // ---------------------------------------------------------------- persistence

        static readonly Dictionary<string, Tracker> loaded = new Dictionary<string, Tracker>();

        static string dir;

        /// <summary>Must be called once from the main thread (Unity APIs aren't usable from the HTTP threads).</summary>
        public static void Init()
        {
            dir = Path.Combine(UnityEngine.Application.persistentDataPath, "RainDash");
            Directory.CreateDirectory(dir);
        }

        public static string Dir
        {
            get { return dir; }
        }

        public static string KeyFor(int slot, string slugcat)
        {
            return "slot" + slot + "_" + slugcat;
        }

        public static Tracker For(int slot, string slugcat)
        {
            string key = KeyFor(slot, slugcat);
            Tracker t;
            if (loaded.TryGetValue(key, out t)) return t;
            t = new Tracker { Key = key };
            string file = Path.Combine(Dir, "tracker_" + key + ".json");
            try
            {
                if (File.Exists(file)) t.Load(File.ReadAllText(file));
            }
            catch (Exception e)
            {
                Plugin.Log.LogWarning("Could not read " + file + ": " + e.Message);
            }
            loaded[key] = t;
            return t;
        }

        void Load(string text)
        {
            var obj = Json.Parse(text) as Dictionary<string, object>;
            if (obj == null) return;
            object v;
            if (obj.TryGetValue("counters", out v) && v is Dictionary<string, object> c)
                foreach (var kv in c) Counters[kv.Key] = Refl.Convert(kv.Value, 0.0);
            if (obj.TryGetValue("maps", out v) && v is Dictionary<string, object> maps)
                foreach (var kv in maps)
                {
                    var m = new Dictionary<string, double>();
                    if (kv.Value is Dictionary<string, object> inner)
                        foreach (var e in inner) m[e.Key] = Refl.Convert(e.Value, 0.0);
                    Maps[kv.Key] = m;
                }
            if (obj.TryGetValue("roomsVisited", out v) && v is List<object> rooms)
                foreach (var r in rooms)
                    if (r is string s) RoomsVisited.Add(s);
        }

        public static void SaveAll()
        {
            foreach (var t in loaded.Values)
            {
                if (!t.Dirty) continue;
                try
                {
                    string file = Path.Combine(Dir, "tracker_" + t.Key + ".json");
                    File.WriteAllText(file + ".tmp", Json.Serialize(t.ToJson()));
                    if (File.Exists(file)) File.Delete(file);
                    File.Move(file + ".tmp", file);
                    t.Dirty = false;
                }
                catch (Exception e)
                {
                    Plugin.Log.LogWarning("Could not save tracker " + t.Key + ": " + e.Message);
                }
            }
        }

        /// <summary>Snapshot of the campaign's save-file stats, cached so the dashboard can show them from the menu.</summary>
        public static void SaveCampaignCache(string key, string json)
        {
            try { File.WriteAllText(Path.Combine(Dir, "campaign_" + key + ".json"), json); }
            catch (Exception e) { Plugin.Log.LogWarning("Could not cache campaign: " + e.Message); }
        }

        public static List<object> ListCachedCampaigns()
        {
            var list = new List<object>();
            try
            {
                foreach (var file in Directory.GetFiles(Dir, "campaign_*.json"))
                {
                    string key = Path.GetFileNameWithoutExtension(file).Substring("campaign_".Length);
                    list.Add(new Dictionary<string, object>
                    {
                        { "key", key },
                        { "updated", (File.GetLastWriteTimeUtc(file) - new DateTime(1970, 1, 1)).TotalMilliseconds },
                    });
                }
            }
            catch (Exception) { }
            return list;
        }

        public static string ReadCachedCampaign(string key)
        {
            foreach (char c in key)
                if (!char.IsLetterOrDigit(c) && c != '_' && c != '-') return null;
            string file = Path.Combine(Dir, "campaign_" + key + ".json");
            return File.Exists(file) ? File.ReadAllText(file) : null;
        }

        public static string ReadTrackerJson(string key)
        {
            foreach (char c in key)
                if (!char.IsLetterOrDigit(c) && c != '_' && c != '-') return null;
            Tracker t;
            if (loaded.TryGetValue(key, out t)) return Json.Serialize(t.ToJson());
            string file = Path.Combine(Dir, "tracker_" + key + ".json");
            return File.Exists(file) ? File.ReadAllText(file) : null;
        }
    }
}
