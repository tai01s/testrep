using System;
using System.IO;
using System.Linq;
using System.Security.Permissions;
using BepInEx;
using BepInEx.Logging;
using UnityEngine;

#pragma warning disable CS0618
[assembly: SecurityPermission(SecurityAction.RequestMinimum, SkipVerification = true)]
#pragma warning restore CS0618

namespace RainDash
{
    [BepInPlugin(ID, "RainDash", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string ID = "raindash";
        public const string Version = "1.0.0";

        public static ManualLogSource Log;
        public static RainDashOptions Options;
        public static string ModPath;
        public static int Port = 8787;

        static HttpServer server;
        static DiscoveryResponder discovery;
        bool initialized, started;

        public static string DashboardUrl()
        {
            return "http://" + FireStickLauncher.BestLocalIp() + ":" + Port + "/";
        }

        void OnEnable()
        {
            Log = Logger;
            On.RainWorld.OnModsInit += RainWorld_OnModsInit;
            On.RainWorld.PostModsInit += RainWorld_PostModsInit;
        }

        void RainWorld_OnModsInit(On.RainWorld.orig_OnModsInit orig, RainWorld self)
        {
            orig(self);
            if (initialized) return;
            initialized = true;
            try
            {
                Tracker.Init();
                AssetExporter.Init();
                Options = new RainDashOptions();
                MachineConnector.SetRegisteredOI(ID, Options);
                Hooks.Apply();
            }
            catch (Exception e)
            {
                Log.LogError(e);
            }
        }

        void RainWorld_PostModsInit(On.RainWorld.orig_PostModsInit orig, RainWorld self)
        {
            orig(self);
            if (started) return;
            started = true;
            try
            {
                ModPath = FindModPath();
                Port = Options != null ? Options.Port.Value : 8787;

                string www = ModPath != null ? Path.Combine(ModPath, "www") : null;
                if (www == null || !Directory.Exists(www))
                {
                    Log.LogError("RainDash www folder not found (looked in " + www + ")");
                    return;
                }

                server = new HttpServer(Port, www);
                server.Start();
                try
                {
                    discovery = new DiscoveryResponder();
                    discovery.Start();
                }
                catch (Exception e)
                {
                    Log.LogWarning("LAN discovery unavailable: " + e.Message);
                }

                Log.LogInfo("RainDash dashboard: " + DashboardUrl());

                if (Options != null && Options.AutoLaunch.Value)
                    FireStickLauncher.LaunchAsync(Options.FireStickIp.Value, Options.AdbPath.Value, Options.WakeTv.Value, null);
            }
            catch (Exception e)
            {
                Log.LogError("RainDash failed to start the dashboard server: " + e);
            }
        }

        static string FindModPath()
        {
            try
            {
                var mod = ModManager.ActiveMods.FirstOrDefault(m => m.id == ID);
                if (mod != null && Directory.Exists(mod.path)) return mod.path;
            }
            catch (Exception) { }
            // plugins/RainDash.dll → mod folder is one level up.
            string dll = typeof(Plugin).Assembly.Location;
            return Path.GetDirectoryName(Path.GetDirectoryName(dll));
        }

        void Update()
        {
            MainThread.Pump();
            if (!started) return;
            AssetExporter.Pump();
            StatsCollector.Tick(Time.unscaledDeltaTime);
        }

        void OnApplicationQuit()
        {
            Tracker.SaveAll();
            if (server != null) server.Stop();
            if (discovery != null) discovery.Stop();
        }
    }
}
