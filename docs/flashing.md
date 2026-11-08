# Flashing the firmware

Boot Tachyon into Linux and connect it over USB with ADB available. Keep power connected throughout. Have an original firmware image and configuration/identity backups available before installing.

From the computer where you built the firmware:

```sh
adb push build/physical-firmware/firmware.bin /var/tmp/syscon-firmware.bin
adb shell
```

Then, in the Tachyon shell:

```sh
sudo flock --nonblock /usr/bin/particle-tachyon-syscon.sh \
  env MSPM0FLASH_CTRL=/usr/bin/mspm0flash_ctrl.sh \
  /usr/bin/mspm0flash -S /dev/ttyHS1 -b 115200 -s -v -v -v -v \
  prog /var/tmp/syscon-firmware.bin
sudo /usr/bin/particle-tachyon-syscon-ctl --timeout 8 VERSION
```

Wait for programming and `VERIFY` to report `OK`. The updater starts the new firmware automatically; no Linux reboot is needed. The version command should return `Version=1.0.52` for the current reconstruction; its version string intentionally matches the original.

Use the updater supplied by Particle's `particle-tachyon-syscon` package; other `mspm0flash` builds can erase configuration and identity data. The lock prevents another packaged update from running at the same time. If flashing fails, keep Linux running and retain the error output before attempting recovery.

To restore the original firmware while Linux is available, copy its image to Tachyon and run the same flash command with that file's path.
