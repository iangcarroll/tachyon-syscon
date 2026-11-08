#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ghidra_root=${SYSCON_GHIDRA_ROOT:-/opt/homebrew/opt/ghidra/libexec}
java_bin=${SYSCON_JAVA:-/opt/homebrew/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home/bin/java}
mkdir -p "$root/build" "$root/analysis"
# Bypass LaunchSupport's attempt to write the user's global Ghidra preferences.
run_ghidra() {
  "$java_bin" -Xmx2G -Djava.awt.headless=true \
    -Djava.system.class.loader=ghidra.GhidraClassLoader \
    -Dapplication.settingsdir="$root/build/ghidra-settings" \
    -Dapplication.cachedir="$root/build/ghidra-cache" \
    --enable-native-access=ALL-UNNAMED \
    -cp "$ghidra_root/Ghidra/Framework/Utility/lib/Utility.jar" \
    ghidra.Ghidra ghidra.app.util.headless.AnalyzeHeadless \
    "$root/build" syscon -scriptPath "$root/tools" "$@"
}
if [ ! -f "$root/build/syscon.gpr" ]; then
  run_ghidra -import "$root/build/reference-firmware/syscon-1.0.52.hex" \
    -processor ARM:LE:32:Cortex -preScript PrepareSyscon.java
fi
run_ghidra -process syscon-1.0.52.hex -preScript AnnotateSyscon.java \
  -postScript ExportSyscon.java "$root/analysis"
