using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;

namespace RainDash
{
    /// <summary>
    /// Opens the RainDash TV app on a Fire Stick over network ADB:
    ///   adb connect IP:5555
    ///   adb -s IP:5555 shell am start -n com.raindash.tv/.MainActivity --es url http://PC:PORT/
    /// </summary>
    public static class FireStickLauncher
    {
        public const string Package = "com.raindash.tv";
        public const string Activity = "com.raindash.tv/.MainActivity";

        static int running;

        public static void LaunchAsync(string ip, string adbPath, bool wake, Action<string> status)
        {
            Action<string> report = msg =>
            {
                Plugin.Log.LogInfo("[FireStick] " + msg);
                if (status != null) MainThread.Post(() => status(msg));
            };

            if (string.IsNullOrEmpty(ip == null ? null : ip.Trim()))
            {
                report("No Fire Stick IP set (Remix options).");
                return;
            }
            if (Interlocked.Exchange(ref running, 1) == 1)
            {
                report("Already launching...");
                return;
            }

            var thread = new Thread(() =>
            {
                try { Launch(ip.Trim(), adbPath, wake, report); }
                catch (Exception e) { report("Failed: " + e.Message); }
                finally { Interlocked.Exchange(ref running, 0); }
            }) { IsBackground = true, Name = "RainDash FireStick" };
            thread.Start();
        }

        static void Launch(string ip, string adbPath, bool wake, Action<string> report)
        {
            string adb = FindAdb(adbPath);
            if (adb == null)
            {
                report("adb.exe not found. Set 'ADB path' in the RainDash options.");
                return;
            }

            string serial = ip.Contains(":") ? ip : ip + ":5555";
            string host = serial.Substring(0, serial.LastIndexOf(':'));
            string url = "http://" + LocalIpFor(host) + ":" + Plugin.Port + "/";

            report("Connecting to " + serial + "...");
            string output;
            Run(adb, "connect " + serial, 15000, out output);
            if (output.IndexOf("connected", StringComparison.OrdinalIgnoreCase) < 0 ||
                output.IndexOf("cannot", StringComparison.OrdinalIgnoreCase) >= 0 ||
                output.IndexOf("failed", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                report("Could not connect: " + output.Trim());
                return;
            }

            if (wake) Run(adb, "-s " + serial + " shell input keyevent KEYCODE_WAKEUP", 8000, out output);

            int code = Run(adb, "-s " + serial + " shell am start -n " + Activity + " --es url " + url, 15000, out output);
            if (output.IndexOf("unauthorized", StringComparison.OrdinalIgnoreCase) >= 0)
                report("Fire Stick says unauthorized: accept the ADB prompt on the TV, then try again.");
            else if (output.IndexOf("Error", StringComparison.Ordinal) >= 0 || code != 0)
                report("Launch failed: " + output.Trim());
            else
                report("Opened RainDash on " + host + " -> " + url);
        }

        public static string FindAdb(string configured)
        {
            if (!string.IsNullOrEmpty(configured))
            {
                configured = configured.Trim().Trim('"');
                if (Directory.Exists(configured)) configured = Path.Combine(configured, AdbExe);
                if (File.Exists(configured)) return configured;
            }

            var candidates = new System.Collections.Generic.List<string>();
            if (Plugin.ModPath != null)
            {
                candidates.Add(Path.Combine(Plugin.ModPath, Path.Combine("platform-tools", AdbExe)));
                candidates.Add(Path.Combine(Plugin.ModPath, AdbExe));
            }
            string local = Environment.GetEnvironmentVariable("LOCALAPPDATA");
            if (!string.IsNullOrEmpty(local))
                candidates.Add(Path.Combine(local, Path.Combine("Android", Path.Combine("Sdk", Path.Combine("platform-tools", AdbExe)))));
            foreach (var env in new[] { "ANDROID_HOME", "ANDROID_SDK_ROOT" })
            {
                string root = Environment.GetEnvironmentVariable(env);
                if (!string.IsNullOrEmpty(root)) candidates.Add(Path.Combine(root, Path.Combine("platform-tools", AdbExe)));
            }
            candidates.Add(@"C:\platform-tools\" + AdbExe);
            candidates.Add(@"C:\adb\" + AdbExe);

            string path = Environment.GetEnvironmentVariable("PATH") ?? "";
            foreach (var dir in path.Split(Path.PathSeparator))
            {
                if (dir.Length == 0) continue;
                try { candidates.Add(Path.Combine(dir.Trim('"'), AdbExe)); } catch (ArgumentException) { }
            }

            foreach (var c in candidates)
                if (File.Exists(c)) return c;
            return null;
        }

        static string AdbExe
        {
            get { return Environment.OSVersion.Platform == PlatformID.Win32NT ? "adb.exe" : "adb"; }
        }

        static int Run(string exe, string args, int timeoutMs, out string output)
        {
            var psi = new ProcessStartInfo(exe, args)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                WindowStyle = ProcessWindowStyle.Hidden
            };
            using (var p = Process.Start(psi))
            {
                // Read asynchronously: "adb connect" may spawn the adb server, which inherits our pipes.
                var stdout = p.StandardOutput.ReadToEndAsync();
                var stderr = p.StandardError.ReadToEndAsync();
                if (!p.WaitForExit(timeoutMs))
                {
                    try { p.Kill(); } catch (Exception) { }
                    output = "timed out";
                    return -1;
                }
                stdout.Wait(2000);
                stderr.Wait(2000);
                output = (stdout.IsCompleted ? stdout.Result : "") + (stderr.IsCompleted ? stderr.Result : "");
                return p.ExitCode;
            }
        }

        /// <summary>The LAN address of this PC as seen from <paramref name="remoteHost"/>.</summary>
        public static string LocalIpFor(string remoteHost)
        {
            try
            {
                using (var s = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp))
                {
                    s.Connect(IPAddress.Parse(remoteHost), 9);
                    return ((IPEndPoint)s.LocalEndPoint).Address.ToString();
                }
            }
            catch (Exception)
            {
                return BestLocalIp();
            }
        }

        public static string BestLocalIp()
        {
            try
            {
                using (var s = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp))
                {
                    s.Connect(IPAddress.Parse("192.168.1.1"), 9);
                    return ((IPEndPoint)s.LocalEndPoint).Address.ToString();
                }
            }
            catch (Exception) { }
            try
            {
                foreach (var a in Dns.GetHostAddresses(Dns.GetHostName()))
                    if (a.AddressFamily == AddressFamily.InterNetwork && !IPAddress.IsLoopback(a)) return a.ToString();
            }
            catch (Exception) { }
            return "127.0.0.1";
        }
    }
}
