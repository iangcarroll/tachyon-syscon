"""Pin artifacts and expose byte-level facts; no device access."""
import hashlib
import json
import re
import struct
from pathlib import Path
from intelhex import IntelHex

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "build/reference-firmware/syscon-1.0.52.bin"
HEX_IMAGE = IMAGE.with_suffix(".hex")
EXPECTED = "5bf027f9655bdabb4870eccee5a39e005a08ce70b8337613672081feecef03f6"


def load_image():
    b = IMAGE.read_bytes()
    if hashlib.sha256(b).hexdigest() != EXPECTED:
        raise ValueError("Reference firmware changed; all addresses require revalidation")
    return b


def cstring(b, offset):
    return b[offset:b.index(0, offset)].decode("ascii")


def command_table(b):
    # Packed 14-byte records: name pointer, Thumb handler pointer, argument
    # policy byte, second flag byte (semantics not yet established), help pointer.
    result = []
    for a in range(0xc419, 0xc61f, 14):
        name, handler, argument_policy, flag, help_ptr = struct.unpack_from("<IIBBI", b, a)
        result.append(dict(record_address=a, name=cstring(b, name),
                           handler=handler & ~1, thumb=bool(handler & 1),
                           argument_policy=argument_policy, flag=flag,
                           help=cstring(b, help_ptr)))
    return result


def main():
    b = load_image()
    h = IntelHex(str(HEX_IMAGE))
    assert all(b[a] == h[a] for a in h.addresses()), "HEX/BIN mismatch"
    result = dict(sha256=EXPECTED, file_size=len(b), version=cstring(b, 0xf7f8),
                  hex_segments=h.segments(), initial_sp=struct.unpack_from("<I", b)[0],
                  reset_handler=struct.unpack_from("<I", b, 4)[0] & ~1,
                  vectors=list(struct.unpack_from("<48I", b)),
                  commands=command_table(b),
                  limits=["Packaged image, not a readback of MCU flash",
                          "Does not include ROM, NONMAIN, or live configuration pages",
                          "Function discovery and decompilation are not proof of understanding"])
    (ROOT / "analysis/manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    strings = [dict(address=m.start(), value=m.group().decode())
               for m in re.finditer(rb"[\x20-\x7e]{4,}", b) if m.start() >= 0xacc0]
    (ROOT / "analysis/strings.json").write_text(json.dumps(strings, indent=2) + "\n")
    print(f"Verified {len(b)} bytes; {len(result['commands'])} command records; version {result['version']}")


if __name__ == "__main__":
    main()
