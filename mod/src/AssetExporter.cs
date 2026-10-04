using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace RainDash
{
    /// <summary>
    /// Pulls sprites (creature kill icons, karma symbols, passage icons...) and the game's bitmap fonts out of
    /// Futile's texture atlases and caches them as PNGs, so the dashboard uses the real Rain World art without
    /// the mod having to redistribute any of it. Rendering has to happen on the main thread.
    /// </summary>
    public static class AssetExporter
    {
        const string CacheVersion = "v1";

        static string iconDir, fontDir;
        static readonly HashSet<string> pending = new HashSet<string>();
        static readonly HashSet<string> failed = new HashSet<string>();
        static bool baseExported;

        public static void Init()
        {
            iconDir = Path.Combine(Tracker.Dir, "icons_" + CacheVersion);
            fontDir = Path.Combine(Tracker.Dir, "fonts_" + CacheVersion);
            Directory.CreateDirectory(iconDir);
            Directory.CreateDirectory(fontDir);
        }

        static string Safe(string name)
        {
            var chars = name.ToCharArray();
            for (int i = 0; i < chars.Length; i++)
                if (!char.IsLetterOrDigit(chars[i]) && chars[i] != '_' && chars[i] != '-' && chars[i] != '.')
                    chars[i] = '_';
            return new string(chars);
        }

        public static string IconPath(string name)
        {
            return Path.Combine(iconDir, Safe(name) + ".png");
        }

        public static void Request(string name)
        {
            if (string.IsNullOrEmpty(name) || iconDir == null) return;
            lock (pending)
            {
                if (failed.Contains(name)) return;
            }
            if (File.Exists(IconPath(name))) return;
            lock (pending) pending.Add(name);
        }

        /// <summary>Called from HTTP threads. Returns the PNG path, exporting it on the main thread if needed.</summary>
        public static string GetIcon(string name)
        {
            string path = IconPath(name);
            if (File.Exists(path)) return path;
            lock (pending)
            {
                if (failed.Contains(name)) return null;
            }
            bool ok = MainThread.Invoke(() => ExportSprite(name, path), 4000, false);
            return ok && File.Exists(path) ? path : null;
        }

        public static string GetFontFile(string fontName, string ext)
        {
            string path = Path.Combine(fontDir, Safe(fontName) + ext);
            if (File.Exists(path)) return path;
            MainThread.Invoke(() => ExportFont(fontName), 4000, false);
            return File.Exists(path) ? path : null;
        }

        /// <summary>Main-thread pump: exports a few queued sprites per frame.</summary>
        public static void Pump()
        {
            if (iconDir == null || Futile.atlasManager == null) return;
            if (!baseExported && Futile.atlasManager.DoesContainElementWithName("Kill_Slugcat"))
            {
                baseExported = true;
                QueueBaseSprites();
            }
            for (int i = 0; i < 4; i++)
            {
                string next = null;
                lock (pending)
                {
                    foreach (var p in pending) { next = p; break; }
                    if (next == null) return;
                    pending.Remove(next);
                }
                ExportSprite(next, IconPath(next));
            }
        }

        static void QueueBaseSprites()
        {
            var names = new List<string>
            {
                "Kill_Slugcat", "Futile_White", "FoodCircleA", "FoodCircleB", "ShelterMarker", "GuidanceSlugcat",
                "Symbol_Rock", "Symbol_Spear", "Symbol_FireSpear", "Symbol_ElectricSpear", "smallKarmaNoRing0",
                "Multiplayer_Death", "Multiplayer_Bones", "Kill_Scavenger", "Kill_Pebbles",
            };
            // Karma symbols as the game draws them (index 0-9, capped at 4 or 9).
            for (int k = 0; k < 10; k++)
            {
                foreach (bool small in new[] { true, false })
                {
                    var sprite = Refl.CallStatic("KarmaMeter", "KarmaSymbolSprite", small,
                        new RWCustom.IntVector2(k, k < 5 ? 4 : 9)) as string;
                    if (sprite != null) names.Add(sprite);
                }
            }
            lock (pending)
                foreach (var n in names)
                    if (!File.Exists(IconPath(n))) pending.Add(n);
        }

        /// <summary>Maps "karma index" → sprite name so the dashboard can ask for /icon/karma/3.</summary>
        public static string KarmaSprite(int k, bool small)
        {
            var sprite = Refl.CallStatic("KarmaMeter", "KarmaSymbolSprite", small,
                new RWCustom.IntVector2(k, k < 5 ? 4 : 9)) as string;
            return sprite;
        }

        static bool ExportSprite(string name, string path)
        {
            try
            {
                if (File.Exists(path)) return true;
                if (!Futile.atlasManager.DoesContainElementWithName(name))
                {
                    lock (pending) failed.Add(name);
                    return false;
                }
                var element = Futile.atlasManager.GetElementWithName(name);
                var tex = ReadElement(element.atlas.texture, element.uvRect);
                if (tex == null) return false;
                File.WriteAllBytes(path, tex.EncodeToPNG());
                UnityEngine.Object.Destroy(tex);
                return true;
            }
            catch (Exception e)
            {
                Plugin.Log.LogWarning("Could not export sprite " + name + ": " + e.Message);
                lock (pending) failed.Add(name);
                return false;
            }
        }

        static Texture2D ReadElement(Texture source, Rect uv)
        {
            int tw = source.width, th = source.height;
            int x = Mathf.RoundToInt(uv.x * tw);
            int y = Mathf.RoundToInt(uv.y * th);
            int w = Mathf.Max(1, Mathf.RoundToInt(uv.width * tw));
            int h = Mathf.Max(1, Mathf.RoundToInt(uv.height * th));

            var rt = RenderTexture.GetTemporary(tw, th, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var previous = RenderTexture.active;
            try
            {
                Graphics.Blit(source, rt);
                RenderTexture.active = rt;
                var tex = new Texture2D(w, h, TextureFormat.ARGB32, false);
                tex.ReadPixels(new Rect(x, y, w, h), 0, 0);
                tex.Apply();
                return tex;
            }
            finally
            {
                RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(rt);
            }
        }

        /// <summary>
        /// Writes fonts/NAME.png (the font's atlas element) and fonts/NAME.json (glyph rects relative to that
        /// image, top-left origin, plus Futile's offsets/advance).
        /// </summary>
        static bool ExportFont(string fontName)
        {
            try
            {
                var font = Futile.atlasManager.GetFontWithName(fontName);
                if (font == null) return false;
                var element = Refl.Get(font, "_element") as FAtlasElement ?? Refl.Get(font, "element") as FAtlasElement;
                if (element == null) return false;
                var texture = element.atlas.texture;
                int tw = texture.width, th = texture.height;
                Rect eu = element.uvRect;

                var tex = ReadElement(texture, eu);
                if (tex == null) return false;
                File.WriteAllBytes(Path.Combine(fontDir, Safe(fontName) + ".png"), tex.EncodeToPNG());
                UnityEngine.Object.Destroy(tex);

                var glyphs = new Dictionary<string, object>();
                var infos = Refl.Get(font, "_charInfos") as IEnumerable ?? Refl.Get(font, "charInfos") as IEnumerable;
                if (infos != null)
                {
                    foreach (var ci in infos)
                    {
                        if (ci == null) continue;
                        int id = Refl.Get(ci, "id", -1);
                        if (id < 0) continue;
                        var uvObj = Refl.Get(ci, "uvRect");
                        if (!(uvObj is Rect uv)) continue;
                        glyphs[id.ToString()] = new List<object>
                        {
                            Mathf.RoundToInt((uv.x - eu.x) * tw),
                            Mathf.RoundToInt((eu.yMax - uv.yMax) * th),
                            Mathf.RoundToInt(uv.width * tw),
                            Mathf.RoundToInt(uv.height * th),
                            Refl.Get(ci, "offsetX", 0f),
                            Refl.Get(ci, "offsetY", 0f),
                            Refl.Get(ci, "xadvance", 0f),
                        };
                    }
                }
                var json = new Dictionary<string, object>
                {
                    { "name", fontName },
                    { "lineHeight", Refl.Get(font, "_lineHeight", Refl.Get(font, "lineHeight", 0f)) },
                    { "glyphs", glyphs },
                };
                File.WriteAllText(Path.Combine(fontDir, Safe(fontName) + ".json"), Json.Serialize(json));
                return glyphs.Count > 0;
            }
            catch (Exception e)
            {
                Plugin.Log.LogWarning("Could not export font " + fontName + ": " + e.Message);
                return false;
            }
        }
    }
}
