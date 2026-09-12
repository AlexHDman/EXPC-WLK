import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

root = Path(__file__).resolve().parents[2]
work = Path(tempfile.mkdtemp(prefix="native updater test ", dir=root / "WhisperKey/logs"))
fixture_source = work / "Fixture.cs"
fixture_source.write_text(r'''using System;
using System.IO;
class Fixture {
    static int Main() {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        if (File.Exists(Path.Combine(root, "fail.marker"))) return 1;
        string token = Environment.GetEnvironmentVariable("EXPC_WLK_UPDATE_TOKEN");
        if (!String.IsNullOrEmpty(token)) {
            string logs = Path.Combine(root, "WhisperKey", "logs");
            Directory.CreateDirectory(logs);
            File.WriteAllText(Path.Combine(logs, "update-ready-" + token), "ready");
        }
        File.WriteAllText(Path.Combine(root, "fixture-started"), "usable");
        return 0;
    }
}
''', encoding="utf-8")
fixture = work / "Fixture.exe"
csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
subprocess.run([str(csc), "/nologo", "/target:winexe", "/out:" + str(fixture), str(fixture_source)], check=True)
for scenario in ("success", "failed-start", "pre-swap-failure"):
    case = work / scenario
    install = case / "Moved portable folder"
    transaction = case / ".EXPC-WLK-update-test"
    stage = transaction / "stage"
    install.mkdir(parents=True)
    stage.mkdir(parents=True)
    (install / "EXPC-WLK.exe").write_bytes(fixture.read_bytes())
    (stage / "EXPC-WLK.exe").write_bytes(fixture.read_bytes())
    for name, value in (("WhisperKey/logs/old.log", b"preserved log"), ("WhisperKey/models/model.bin", b"preserved model")):
        path = install / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    if scenario == "failed-start":
        (stage / "fail.marker").write_text("fail")
    token = uuid.uuid4().hex
    if scenario == "pre-swap-failure":
        Path(str(install) + ".previous-" + token).mkdir()
    helper = transaction / "PortableUpdater.exe"
    helper.write_bytes((root / "WhisperKey/config/PortableUpdater.exe").read_bytes())
    result = subprocess.run([str(helper), str(install), str(stage), "2147483647", "2147483646", token, "--quiet"],
                            creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
    assert result.returncode == (0 if scenario == "success" else 1), scenario
    assert (install / "EXPC-WLK.exe").exists()
    assert (install / "WhisperKey/logs/old.log").read_bytes() == b"preserved log"
    assert (install / "WhisperKey/models/model.bin").read_bytes() == b"preserved model"
    if scenario in ("failed-start", "pre-swap-failure"):
        time.sleep(.3)
        assert (install / "fixture-started").exists(), "Rollback did not start"
        assert not (install / "fail.marker").exists()
    print("PASS native updater:", scenario, "; moved/spaced path; preserved logs/models")
print("Native test evidence:", work)
