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
sudo /usr/bin/particle-tachyon-syscon-ctl --timeout 8 VERSION
```

Wait for programming and `VERIFY` to report `OK`, followed by `Syscon upgrade done.` The updater starts the new firmware automatically; no Linux reboot is needed. The version command should return `Version=1.0.52` for the current reconstruction; its version string intentionally matches the original, which is why installation uses `--force`.

These commands use Particle's `particle-tachyon-syscon` 1.1.1-1 package. Its script locks out concurrent updates. Other `mspm0flash` builds can erase configuration and identity data. If flashing fails, keep Linux running and retain the error output before attempting recovery.

To restore the original firmware while Linux is available, copy its image to Tachyon and run the same flash command with that file's path.
