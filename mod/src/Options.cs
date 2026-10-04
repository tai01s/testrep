using Menu.Remix.MixedUI;
using UnityEngine;

namespace RainDash
{
    /// <summary>Remix menu (Options → Mods → RainDash).</summary>
    public class RainDashOptions : OptionInterface
    {
        public readonly Configurable<bool> AutoLaunch;
        public readonly Configurable<string> FireStickIp;
        public readonly Configurable<string> AdbPath;
        public readonly Configurable<int> Port;
        public readonly Configurable<bool> WakeTv;

        OpLabel statusLabel;

        public RainDashOptions()
        {
            AutoLaunch = config.Bind("autoLaunchFireStick", true,
                new ConfigurableInfo("When Rain World starts, open the RainDash app on your Fire Stick (uses ADB).", null, "",
                    "Auto-launch on Fire Stick"));
            FireStickIp = config.Bind("fireStickIp", "",
                new ConfigurableInfo("IP address of your Fire Stick (Settings > My Fire TV > About > Network).", null, "",
                    "Fire Stick IP"));
            AdbPath = config.Bind("adbPath", "",
                new ConfigurableInfo("Full path to adb.exe. Leave empty to search PATH, the mod folder and the Android SDK.", null, "",
                    "ADB path"));
            Port = config.Bind("port", 8787,
                new ConfigurableInfo("Port the dashboard is served on. Restart the game after changing.",
                    new ConfigAcceptableRange<int>(1024, 65000), "", "Dashboard port"));
            WakeTv = config.Bind("wakeTv", true,
                new ConfigurableInfo("Send a wake-up key to the Fire Stick before launching (can turn the TV on via HDMI-CEC).", null, "",
                    "Wake TV"));
        }

        public override void Initialize()
        {
            base.Initialize();
            var tab = new OpTab(this, "RainDash");
            Tabs = new[] { tab };

            float y = 540f;
            tab.AddItems(new OpLabel(new Vector2(20f, y), new Vector2(560f, 40f), "RainDash", FLabelAlignment.Left, true));
            y -= 40f;
            tab.AddItems(new OpLabel(new Vector2(20f, y), new Vector2(560f, 24f),
                "Dashboard: " + Plugin.DashboardUrl(), FLabelAlignment.Left));

            y -= 50f;
            tab.AddItems(
                new OpCheckBox(AutoLaunch, new Vector2(20f, y)) { description = AutoLaunch.info.description },
                new OpLabel(new Vector2(60f, y), new Vector2(300f, 24f), "Auto-launch app on Fire Stick", FLabelAlignment.Left));

            y -= 40f;
            tab.AddItems(
                new OpCheckBox(WakeTv, new Vector2(20f, y)) { description = WakeTv.info.description },
                new OpLabel(new Vector2(60f, y), new Vector2(300f, 24f), "Wake the TV before launching", FLabelAlignment.Left));

            y -= 50f;
            tab.AddItems(
                new OpLabel(new Vector2(20f, y), new Vector2(150f, 24f), "Fire Stick IP", FLabelAlignment.Left),
                new OpTextBox(FireStickIp, new Vector2(180f, y), 200f) { description = FireStickIp.info.description });

            y -= 40f;
            tab.AddItems(
                new OpLabel(new Vector2(20f, y), new Vector2(150f, 24f), "ADB path", FLabelAlignment.Left),
                new OpTextBox(AdbPath, new Vector2(180f, y), 380f) { description = AdbPath.info.description });

            y -= 40f;
            tab.AddItems(
                new OpLabel(new Vector2(20f, y), new Vector2(150f, 24f), "Dashboard port", FLabelAlignment.Left),
                new OpUpdown(Port, new Vector2(180f, y - 4f), 100f) { description = Port.info.description });

            y -= 60f;
            var launch = new OpSimpleButton(new Vector2(20f, y), new Vector2(200f, 30f), "Launch on Fire Stick now")
            {
                description = "Saves nothing; uses the values currently typed above."
            };
            launch.OnClick += _ =>
            {
                FireStickLauncher.LaunchAsync(FireStickIp.Value, AdbPath.Value, WakeTv.Value,
                    msg => statusLabel.text = msg);
            };
            statusLabel = new OpLabel(new Vector2(240f, y + 3f), new Vector2(340f, 24f), "", FLabelAlignment.Left);
            tab.AddItems(launch, statusLabel);

            y -= 60f;
            tab.AddItems(new OpLabel(new Vector2(20f, y - 60f), new Vector2(560f, 80f),
                "Setup: enable ADB debugging on the Fire Stick (Settings > My Fire TV > Developer Options),\n" +
                "install the RainDash TV app, put platform-tools (adb.exe) somewhere this mod can find it,\n" +
                "then accept the 'Allow USB debugging?' prompt on the TV the first time.",
                FLabelAlignment.Left));
        }
    }
}
