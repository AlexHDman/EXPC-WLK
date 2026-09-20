using System;
using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: System.Reflection.AssemblyTitle("EXPC-WLK")]
[assembly: System.Reflection.AssemblyProduct("EXPC-WLK")]
[assembly: System.Reflection.AssemblyDescription("EXPC-WLK installed launcher")]
[assembly: System.Reflection.AssemblyCompany("EXPC-WLK")]

internal static class InstalledLauncher
{
    private const string Product = "EXPC-WLK";
    private const string AutostartName = "EXPC-WLK";

    [STAThread]
    private static int Main(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        string logDir = Path.Combine(appData, "whisperkey");
        try
        {
            if (args.Length >= 1 && (args[0] == "--enable-autostart" || args[0] == "--disable-autostart"))
            {
                using (RegistryKey key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run"))
                {
                    if (args[0] == "--enable-autostart")
                        key.SetValue(AutostartName, "\"" + Application.ExecutablePath + "\"");
                    else
                        key.DeleteValue(AutostartName, false);
                }
                if (args.Length < 2 || args[1] != "--quiet")
                    MessageBox.Show(args[0] == "--enable-autostart" ? "EXPC-WLK autostart enabled." : "EXPC-WLK autostart disabled.", Product);
                return 0;
            }

            string updateToken = null, updateReceipt = null;
            bool testMode = false;
            if (args.Length != 0)
            {
                if (args.Length == 1 && args[0] == "--test")
                    testMode = true;
                else if ((args.Length != 4 && args.Length != 5) ||
                    args[0] != "--installed-update-token" ||
                    args[2] != "--installed-update-receipt" ||
                    (args.Length == 5 && args[4] != "--test") ||
                    !Regex.IsMatch(args[1], "^[a-f0-9]{32}$"))
                    throw new ArgumentException("Invalid installed update launch arguments.");
                else
                {
                    updateToken = args[1];
                    updateReceipt = Path.GetFullPath(args[3]);
                    testMode = args.Length == 5;
                    string expectedReceipt = Path.Combine(appData, "whisperkey",
                        "installed-update-ready-" + updateToken + ".json");
                    if (!String.Equals(updateReceipt, expectedReceipt, StringComparison.OrdinalIgnoreCase))
                        throw new ArgumentException("Invalid installed update receipt path.");
                }
            }

            bool created;
            using (Mutex guard = new Mutex(true, @"Local\WhisperKeyInstalledLauncher", out created))
            {
                bool existingApp = false;
                try { using (Mutex app = Mutex.OpenExisting("WhisperKeyLocal_SingleInstance")) { existingApp = true; } }
                catch (WaitHandleCannotBeOpenedException) { }
                if (!created || (existingApp && !testMode))
                {
                    Directory.CreateDirectory(logDir);
                    File.AppendAllText(Path.Combine(logDir, "launcher.log"), DateTime.Now.ToString("o") + " ALREADY_RUNNING\n");
                    MessageBox.Show("EXPC-WLK is already running. Use its tray icon.", Product, MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return 0;
                }

                string python = Path.Combine(root, "runtime", "pythonw.exe");
                string boot = Path.Combine(root, "app", "installed_boot.py");
                if (!File.Exists(python) || !File.Exists(boot))
                    throw new FileNotFoundException("Installed runtime is incomplete. Repair EXPC-WLK from Apps & Features.");
                string pythonArguments = "-I \"" + boot + "\"";
                if (updateToken != null)
                    pythonArguments += " --installed-update-token " + updateToken +
                        " --installed-update-receipt \"" + updateReceipt + "\"";
                if (testMode) pythonArguments += " --test";
                ProcessStartInfo info = new ProcessStartInfo(python, pythonArguments);
                info.WorkingDirectory = root;
                info.UseShellExecute = false;
                info.CreateNoWindow = true;
                info.WindowStyle = ProcessWindowStyle.Hidden;
                using (EventWaitHandle restart = new EventWaitHandle(false, EventResetMode.ManualReset, @"Local\WhisperKeyInstalledRestart"))
                {
                    while (true)
                    {
                        restart.Reset();
                        using (Process child = Process.Start(info))
                        {
                            child.WaitForExit();
                            if (!restart.WaitOne(0)) return child.ExitCode;
                        }
                    }
                }
            }
        }
        catch (Exception ex)
        {
            string entry = DateTime.Now.ToString("o") + " ERROR " + ex + "\n";
            try
            {
                Directory.CreateDirectory(logDir);
                File.AppendAllText(Path.Combine(logDir, "launcher.log"), entry);
            }
            catch
            {
                try { File.AppendAllText(Path.Combine(Path.GetTempPath(), "EXPC-WLK-launcher.log"), entry); }
                catch { }
            }
            MessageBox.Show(ex.Message, Product, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
