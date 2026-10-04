using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace RainDash
{
    /// <summary>
    /// Tiny JSON serializer/parser. Objects are Dictionary&lt;string, object&gt;, arrays are List&lt;object&gt;,
    /// numbers parse as double. Good enough for the dashboard API and the tracker save files.
    /// </summary>
    public static class Json
    {
        public static string Serialize(object value)
        {
            var sb = new StringBuilder(4096);
            Write(sb, value);
            return sb.ToString();
        }

        static void Write(StringBuilder sb, object v)
        {
            if (v == null) { sb.Append("null"); return; }
            if (v is string s) { WriteString(sb, s); return; }
            if (v is bool b) { sb.Append(b ? "true" : "false"); return; }
            if (v is float f) { WriteNumber(sb, f); return; }
            if (v is double d) { WriteNumber(sb, d); return; }
            if (v is int || v is long || v is short || v is byte || v is uint || v is ulong)
            {
                sb.Append(Convert.ToString(v, CultureInfo.InvariantCulture));
                return;
            }
            if (v is IDictionary dict)
            {
                sb.Append('{');
                bool first = true;
                foreach (DictionaryEntry e in dict)
                {
                    if (!first) sb.Append(',');
                    first = false;
                    WriteString(sb, Convert.ToString(e.Key, CultureInfo.InvariantCulture));
                    sb.Append(':');
                    Write(sb, e.Value);
                }
                sb.Append('}');
                return;
            }
            if (v is IEnumerable list)
            {
                sb.Append('[');
                bool first = true;
                foreach (var item in list)
                {
                    if (!first) sb.Append(',');
                    first = false;
                    Write(sb, item);
                }
                sb.Append(']');
                return;
            }
            WriteString(sb, v.ToString());
        }

        static void WriteNumber(StringBuilder sb, double d)
        {
            if (double.IsNaN(d) || double.IsInfinity(d)) { sb.Append('0'); return; }
            sb.Append(d.ToString("0.####", CultureInfo.InvariantCulture));
        }

        static void WriteString(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }

        public static object Parse(string text)
        {
            int i = 0;
            var v = ParseValue(text, ref i);
            return v;
        }

        static void SkipWs(string t, ref int i)
        {
            while (i < t.Length && char.IsWhiteSpace(t[i])) i++;
        }

        static object ParseValue(string t, ref int i)
        {
            SkipWs(t, ref i);
            if (i >= t.Length) throw new FormatException("Unexpected end of JSON");
            char c = t[i];
            if (c == '{')
            {
                i++;
                var obj = new Dictionary<string, object>();
                SkipWs(t, ref i);
                if (t[i] == '}') { i++; return obj; }
                while (true)
                {
                    SkipWs(t, ref i);
                    string key = ParseString(t, ref i);
                    SkipWs(t, ref i);
                    if (t[i] != ':') throw new FormatException("Expected ':'");
                    i++;
                    obj[key] = ParseValue(t, ref i);
                    SkipWs(t, ref i);
                    if (t[i] == ',') { i++; continue; }
                    if (t[i] == '}') { i++; return obj; }
                    throw new FormatException("Expected ',' or '}'");
                }
            }
            if (c == '[')
            {
                i++;
                var list = new List<object>();
                SkipWs(t, ref i);
                if (t[i] == ']') { i++; return list; }
                while (true)
                {
                    list.Add(ParseValue(t, ref i));
                    SkipWs(t, ref i);
                    if (t[i] == ',') { i++; continue; }
                    if (t[i] == ']') { i++; return list; }
                    throw new FormatException("Expected ',' or ']'");
                }
            }
            if (c == '"') return ParseString(t, ref i);
            if (t.Length - i >= 4 && string.CompareOrdinal(t, i, "true", 0, 4) == 0) { i += 4; return true; }
            if (t.Length - i >= 5 && string.CompareOrdinal(t, i, "false", 0, 5) == 0) { i += 5; return false; }
            if (t.Length - i >= 4 && string.CompareOrdinal(t, i, "null", 0, 4) == 0) { i += 4; return null; }
            int start = i;
            while (i < t.Length && "+-0123456789.eE".IndexOf(t[i]) >= 0) i++;
            if (start == i) throw new FormatException("Unexpected character '" + c + "'");
            return double.Parse(t.Substring(start, i - start), CultureInfo.InvariantCulture);
        }

        static string ParseString(string t, ref int i)
        {
            if (t[i] != '"') throw new FormatException("Expected string");
            i++;
            var sb = new StringBuilder();
            while (i < t.Length)
            {
                char c = t[i++];
                if (c == '"') return sb.ToString();
                if (c != '\\') { sb.Append(c); continue; }
                char e = t[i++];
                switch (e)
                {
                    case 'n': sb.Append('\n'); break;
                    case 'r': sb.Append('\r'); break;
                    case 't': sb.Append('\t'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'u':
                        sb.Append((char)int.Parse(t.Substring(i, 4), NumberStyles.HexNumber));
                        i += 4;
                        break;
                    default: sb.Append(e); break;
                }
            }
            throw new FormatException("Unterminated string");
        }
    }
}
