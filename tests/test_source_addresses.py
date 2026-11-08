"""Architectural lint plus executable layout tests guard private-address regressions."""
import random
from audit_source_addresses import audit,violations


def test_production_sources_have_no_private_address_literals():
    assert audit()==[]


def test_lint_rejects_private_ram_and_rom_but_accepts_hardware_contracts():
    rng=random.Random(129)
    for _ in range(40):
        ram=rng.randrange(0x20000001,0x20001000)
        rom=rng.randrange(1,0xf7f8)
        for value in [str(ram),hex(ram)]:
            assert violations(f'const unsigned state = {value};')
        assert violations(f'char *s=(char *){rom};')
        assert violations(f'LOG(TEXT({rom}));')
    for address in [0x400a0000,0x400b0400,0xe000ed0c,0xf800,0xfc00]:
        assert not violations(f'*(volatile unsigned *)(uintptr_t){address:#x}=0;')
    assert not violations('mask |= 0x20000000u; /* original 0x20000258 */')
    assert not violations('const char *note="old TEXT(0xae64)";')


def test_every_physical_build_input_is_checked_including_extra_sources(tmp_path):
    from build_physical_firmware import production_sources
    sources=production_sources()
    assert sources
    for source in sources:
        path=tmp_path/source;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('')
    assert audit(tmp_path)==[]
    rng=random.Random(970)
    for source in sources:
        path=tmp_path/source
        address=rng.randrange(0x20000001,0x20001000)
        path.write_text(f'unsigned private_state={address:#x};')
        findings=audit(tmp_path)
        assert len(findings)==1 and findings[0][0]==source
        path.write_text('')
    assert audit(tmp_path)==[]
