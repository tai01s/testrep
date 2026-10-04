using System;
using System.Collections.Generic;
using System.Reflection;

namespace RainDash
{
    /// <summary>
    /// Reflection helpers. Many campaign-specific fields (Artificer pyro counter, Saint god timer, Hunter
    /// cycle limit...) differ between game versions, so we read them by name and fall back gracefully
    /// instead of hard-linking and crashing the whole mod when one gets renamed.
    /// </summary>
    public static class Refl
    {
        const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance |
                                 BindingFlags.Static | BindingFlags.DeclaredOnly;

        static readonly Dictionary<string, MemberInfo> cache = new Dictionary<string, MemberInfo>();
        static readonly Dictionary<string, Type> typeCache = new Dictionary<string, Type>();

        static MemberInfo Find(Type type, string name)
        {
            string key = type.FullName + "::" + name;
            lock (cache)
            {
                if (cache.TryGetValue(key, out var cached)) return cached;
            }
            MemberInfo found = null;
            for (var t = type; t != null && found == null; t = t.BaseType)
            {
                var f = t.GetField(name, All);
                if (f != null) { found = f; break; }
                var p = t.GetProperty(name, All);
                if (p != null && p.GetIndexParameters().Length == 0) { found = p; break; }
            }
            lock (cache) cache[key] = found;
            return found;
        }

        public static bool Has(object obj, string name)
        {
            return obj != null && Find(obj.GetType(), name) != null;
        }

        public static object Get(object obj, string name)
        {
            if (obj == null) return null;
            try
            {
                var m = Find(obj.GetType(), name);
                if (m is FieldInfo f) return f.GetValue(obj);
                if (m is PropertyInfo p) return p.GetValue(obj, null);
            }
            catch (Exception) { }
            return null;
        }

        public static T Get<T>(object obj, string name, T fallback)
        {
            return Convert<T>(Get(obj, name), fallback);
        }

        public static T Convert<T>(object v, T fallback)
        {
            if (v == null) return fallback;
            if (v is T t) return t;
            try
            {
                if (v is IConvertible) return (T)System.Convert.ChangeType(v, typeof(T));
            }
            catch (Exception) { }
            return fallback;
        }

        public static Type FindType(string fullName)
        {
            lock (typeCache)
            {
                if (typeCache.TryGetValue(fullName, out var cached)) return cached;
            }
            Type found = null;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    found = asm.GetType(fullName, false);
                    if (found != null) break;
                }
                catch (Exception) { }
            }
            lock (typeCache) typeCache[fullName] = found;
            return found;
        }

        public static object GetStatic(string typeName, string member)
        {
            var t = FindType(typeName);
            if (t == null) return null;
            try
            {
                var m = Find(t, member);
                if (m is FieldInfo f) return f.GetValue(null);
                if (m is PropertyInfo p) return p.GetValue(null, null);
            }
            catch (Exception) { }
            return null;
        }

        public static object CallStatic(string typeName, string method, params object[] args)
        {
            if (args == null) args = new object[] { null };
            var t = FindType(typeName);
            if (t == null) return null;
            try
            {
                foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static))
                {
                    if (m.Name != method || m.GetParameters().Length != args.Length) continue;
                    return m.Invoke(null, args);
                }
            }
            catch (Exception) { }
            return null;
        }

        /// <summary>Unwraps a Remix Configurable&lt;T&gt; (or anything with a Value property).</summary>
        public static T ConfigValue<T>(object configurable, T fallback)
        {
            return Get(configurable, "Value", fallback);
        }
    }
}
