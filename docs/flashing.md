# Flashing the firmware

Boot Tachyon into Linux and connect it over USB with ADB available. Keep power connected throughout. Have an original firmware image and configuration/identity backups available before installing.

From the computer where you built the firmware:

```sh
adb push build/physical-firmware/firmware.bin /var/tmp/syscon-firmware.bin
adb shell
```

Then, in the Tachyon shell:

```sh
sudo /usr/bin/particle-tachyon-syscon.sh upgrade --force --firmware /var/tmp/syscon-firmware.bin
sudo /usr/bin/particle-tachyon-syscon.sh syscon_version
```

Wait for programming and `VERIFY` to report `OK`, followed by `Syscon upgrade done.` The updater starts the new firmware automatically; no Linux reboot is needed. The version command should return `1.0.52` for the current reconstruction. `--force` is necessary because it deliberately uses the same version as the original firmware.

These commands use the `--firmware` option in Particle's `particle-tachyon-syscon` 1.1.1-1 package. Use Particle's supplied updater; other `mspm0flash` builds can erase configuration and identity data. If flashing fails, keep Linux running and retain the error output before attempting recovery.

To restore the original firmware while Linux is available, copy its image to Tachyon and run the same upgrade command with that file's path.
