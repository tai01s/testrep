using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace RainDash
{
    /// <summary>
    /// Minimal HTTP/1.1 server (GET only) on a TcpListener. Mono's HttpListener works too, but a raw socket
    /// server avoids URL-ACL/admin issues on Windows and is all the dashboard needs.
    /// </summary>
    public class HttpServer
    {
        readonly int port;
        readonly string wwwRoot;
        TcpListener listener;
        Thread acceptThread;
        volatile bool running;

        public HttpServer(int port, string wwwRoot)
        {
            this.port = port;
            this.wwwRoot = wwwRoot;
        }

        public void Start()
        {
            listener = new TcpListener(IPAddress.Any, port);
            listener.Start();
            running = true;
            acceptThread = new Thread(AcceptLoop) { IsBackground = true, Name = "RainDash HTTP" };
            acceptThread.Start();
            Plugin.Log.LogInfo("Dashboard serving " + wwwRoot + " on port " + port);
        }

        public void Stop()
        {
            running = false;
            try { listener.Stop(); } catch (Exception) { }
        }

        void AcceptLoop()
        {
            while (running)
            {
                try
                {
                    var client = listener.AcceptTcpClient();
                    ThreadPool.QueueUserWorkItem(_ => Handle(client));
                }
                catch (Exception e)
                {
                    if (!running) break;
                    Plugin.Log.LogWarning("HTTP accept failed: " + e.Message);
                    Thread.Sleep(200);
                }
            }
        }

        void Handle(TcpClient client)
        {
            using (client)
            {
                try
                {
                    client.ReceiveTimeout = 5000;
                    client.SendTimeout = 10000;
                    var stream = client.GetStream();
                    string requestLine = ReadHead(stream);
                    if (requestLine == null) return;
                    var parts = requestLine.Split(' ');
                    if (parts.Length < 2) return;
                    if (parts[0] == "OPTIONS")
                    {
                        Send(stream, 204, "text/plain", new byte[0]);
                        return;
                    }
                    if (parts[0] != "GET" && parts[0] != "HEAD")
                    {
                        Send(stream, 405, "text/plain", Encoding.UTF8.GetBytes("GET only"));
                        return;
                    }
                    string target = parts[1];
                    string query = "";
                    int q = target.IndexOf('?');
                    if (q >= 0)
                    {
                        query = target.Substring(q + 1);
                        target = target.Substring(0, q);
                    }
                    Route(stream, Uri.UnescapeDataString(target), ParseQuery(query), parts[0] == "HEAD");
                }
                catch (Exception e)
                {
                    if (!(e is IOException) && !(e is SocketException))
                        Plugin.Log.LogWarning("HTTP request failed: " + e);
                }
            }
        }

        /// <summary>Reads the request head (until a blank line) and returns the request line.</summary>
        static string ReadHead(NetworkStream stream)
        {
            var sb = new StringBuilder();
            int prev2 = 0, prev1 = 0;
            while (sb.Length < 16384)
            {
                int b = stream.ReadByte();
                if (b < 0) break;
                sb.Append((char)b);
                if (prev2 == '\n' && prev1 == '\r' && b == '\n') break;
                if (prev1 == '\n' && b == '\n') break;
                prev2 = prev1;
                prev1 = b;
            }
            string head = sb.ToString();
            int end = head.IndexOf('\n');
            return end > 0 ? head.Substring(0, end).TrimEnd('\r') : null;
        }

        static Dictionary<string, string> ParseQuery(string query)
        {
            var d = new Dictionary<string, string>();
            foreach (var pair in query.Split('&'))
            {
                if (pair.Length == 0) continue;
                int eq = pair.IndexOf('=');
                if (eq < 0) d[Uri.UnescapeDataString(pair)] = "";
                else d[Uri.UnescapeDataString(pair.Substring(0, eq))] = Uri.UnescapeDataString(pair.Substring(eq + 1).Replace('+', ' '));
            }
            return d;
        }

        void Route(NetworkStream s, string path, Dictionary<string, string> query, bool head)
        {
            string slug;
            query.TryGetValue("slug", out slug);

            if (path == "/api/state")
            {
                SendJson(s, StatsCollector.StateJson, head);
                return;
            }
            if (path == "/api/regions")
            {
                SendJson(s, MapExporter.RegionListJson(slug), head);
                return;
            }
            if (path.StartsWith("/api/map/"))
            {
                string json = MapExporter.RegionJson(path.Substring("/api/map/".Length), slug);
                if (json == null) NotFound(s);
                else SendJson(s, json, head, "public, max-age=600");
                return;
            }
            if (path == "/api/campaigns")
            {
                SendJson(s, Json.Serialize(Tracker.ListCachedCampaigns()), head);
                return;
            }
            if (path.StartsWith("/api/campaign/"))
            {
                string key = path.Substring("/api/campaign/".Length);
                string campaign = Tracker.ReadCachedCampaign(key);
                string tracker = MainThread.Invoke(() => Tracker.ReadTrackerJson(key), 3000, null);
                if (campaign == null) NotFound(s);
                else SendJson(s, "{\"campaign\":" + campaign + ",\"tracker\":" + (tracker ?? "null") + "}", head);
                return;
            }
            if (path.StartsWith("/icon/karma/"))
            {
                // /icon/karma/{index}[/big]
                var bits = path.Substring("/icon/karma/".Length).Split('/');
                int k;
                string sprite = int.TryParse(bits[0], out k) && k >= 0 && k < 10
                    ? AssetExporter.KarmaSprite(k, bits.Length < 2 || bits[1] != "big")
                    : null;
                SendIcon(s, sprite, head);
                return;
            }
            if (path.StartsWith("/icon/"))
            {
                string name = path.Substring("/icon/".Length);
                if (name.EndsWith(".png")) name = name.Substring(0, name.Length - 4);
                SendIcon(s, name, head);
                return;
            }
            if (path.StartsWith("/font/"))
            {
                string name = path.Substring("/font/".Length);
                string ext = Path.GetExtension(name);
                string file = AssetExporter.GetFontFile(Path.GetFileNameWithoutExtension(name), ext);
                if (file == null) NotFound(s);
                else SendFile(s, file, head, "public, max-age=86400");
                return;
            }

            // Static dashboard files.
            if (path == "/" || path.Length == 0) path = "/index.html";
            string full = Path.GetFullPath(Path.Combine(wwwRoot, path.TrimStart('/')));
            string root = Path.GetFullPath(wwwRoot).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            if (!full.StartsWith(root, StringComparison.OrdinalIgnoreCase) || !File.Exists(full))
            {
                NotFound(s);
                return;
            }
            SendFile(s, full, head, "no-cache");
        }

        void SendIcon(NetworkStream s, string sprite, bool head)
        {
            string file = sprite != null ? AssetExporter.GetIcon(sprite) : null;
            if (file == null) NotFound(s);
            else SendFile(s, file, head, "public, max-age=86400");
        }

        static void NotFound(NetworkStream s)
        {
            Send(s, 404, "text/plain", Encoding.UTF8.GetBytes("not found"));
        }

        static void SendJson(NetworkStream s, string json, bool head, string cache = "no-store")
        {
            Send(s, 200, "application/json; charset=utf-8", Encoding.UTF8.GetBytes(json ?? "null"), head, cache);
        }

        static void SendFile(NetworkStream s, string file, bool head, string cache)
        {
            Send(s, 200, Mime(file), File.ReadAllBytes(file), head, cache);
        }

        static string Mime(string file)
        {
            switch (Path.GetExtension(file).ToLowerInvariant())
            {
                case ".html": return "text/html; charset=utf-8";
                case ".js": return "application/javascript; charset=utf-8";
                case ".css": return "text/css; charset=utf-8";
                case ".json": return "application/json; charset=utf-8";
                case ".png": return "image/png";
                case ".svg": return "image/svg+xml";
                case ".ttf": return "font/ttf";
                case ".otf": return "font/otf";
                case ".woff": return "font/woff";
                case ".woff2": return "font/woff2";
                default: return "application/octet-stream";
            }
        }

        static void Send(NetworkStream s, int status, string type, byte[] body, bool head = false, string cache = "no-store")
        {
            string reason = status == 200 ? "OK" : status == 204 ? "No Content" : status == 404 ? "Not Found" : "Error";
            var header = new StringBuilder();
            header.Append("HTTP/1.1 ").Append(status).Append(' ').Append(reason).Append("\r\n");
            header.Append("Content-Type: ").Append(type).Append("\r\n");
            header.Append("Content-Length: ").Append(body.Length).Append("\r\n");
            header.Append("Cache-Control: ").Append(cache).Append("\r\n");
            header.Append("Access-Control-Allow-Origin: *\r\n");
            header.Append("Connection: close\r\n\r\n");
            var bytes = Encoding.ASCII.GetBytes(header.ToString());
            s.Write(bytes, 0, bytes.Length);
            if (!head) s.Write(body, 0, body.Length);
            s.Flush();
        }
    }

    /// <summary>
    /// LAN discovery so the TV app can find the PC without typing an IP: the app broadcasts
    /// "RAINDASH_DISCOVER" on UDP 47812 and we answer "RAINDASH http://ip:port/".
    /// </summary>
    public class DiscoveryResponder
    {
        public const int DiscoveryPort = 47812;
        UdpClient udp;
        volatile bool running;

        public void Start()
        {
            udp = new UdpClient(new IPEndPoint(IPAddress.Any, DiscoveryPort));
            udp.EnableBroadcast = true;
            running = true;
            new Thread(Loop) { IsBackground = true, Name = "RainDash discovery" }.Start();
        }

        public void Stop()
        {
            running = false;
            try { udp.Close(); } catch (Exception) { }
        }

        void Loop()
        {
            while (running)
            {
                try
                {
                    var from = new IPEndPoint(IPAddress.Any, 0);
                    var data = udp.Receive(ref from);
                    if (Encoding.ASCII.GetString(data).Trim() != "RAINDASH_DISCOVER") continue;
                    string ip = FireStickLauncher.LocalIpFor(from.Address.ToString());
                    var reply = Encoding.ASCII.GetBytes("RAINDASH http://" + ip + ":" + Plugin.Port + "/");
                    udp.Send(reply, reply.Length, from);
                }
                catch (Exception e)
                {
                    if (!running) break;
                    Plugin.Log.LogWarning("Discovery error: " + e.Message);
                    Thread.Sleep(200);
                }
            }
        }
    }
}
