"""Measure exact machine-code reproduction per implemented function.

Never reports a partial result as a matching/releasable firmware image.
"""
import json
import subprocess
from inventory import ROOT, load_image


def main():
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-Os',
                    '-ffunction-sections','-fdata-sections','-ffreestanding',
                    '-I',str(ROOT/'include'),'-c',str(ROOT/'tests/models/config.c'),
                    '-o',str(ROOT/'build/config.arm.o')],check=True)
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',
                    '--only-section=.text.syscon_checksum31',
                    str(ROOT/'build/config.arm.o'),str(ROOT/'build/checksum31.bin')],check=True)
    b=load_image()
    compiled=(ROOT/'build/checksum31.bin').read_bytes()
    result=dict(function='syscon_checksum31', original_address=0x282c,
                original_size=20,reconstructed_size=len(compiled),
                exact_bytes=compiled==b[0x282c:0x2840],
                compiler=subprocess.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
                whole_firmware_match=False,flash_candidate=False)
    (ROOT/'analysis/binary-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not result['exact_bytes']: raise SystemExit('Checksum routine differs; inspect toolchain/codegen')


if __name__=='__main__': main()
