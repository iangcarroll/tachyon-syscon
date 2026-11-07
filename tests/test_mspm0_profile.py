"""Independent TI header/pack cross-checks for emulator register metadata."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
import pytest
from mspm0.profile import ROOT,PROFILE,IRQ,SVD,registers

REF=ROOT/'references/ti-mspm0'
DEVICE=(REF/'mspm0l130x.h').read_text()
BASES={n:int(v,16) for n,v in re.findall(r'#define\s+(\w+)_BASE\s+\((0x[\da-fA-F]+)U\)',DEVICE)}
TYPES={n:t for t,n in re.findall(r'static\s+(\w+)_Regs\s*\*\s*const\s+(\w+)\s*=',DEVICE)}
ACCESS={'__IO':'read-write','__I':'read-only','__O':'write-only'}
DECL=r'(__IO|__I|__O)\s+uint(\d+)_t\s+(\w+)(?:\[(\d+)\])?;\s*/\*[^\n]*?@\s*(0x[\da-fA-F]+)'

def fields(header,structure):
    text=(REF/header).read_text()
    for body,name in re.findall(r'typedef struct\s*\{(.*?)\}\s*(\w+);',text,re.S):
        if name==structure:
            return [(ACCESS[a],int(w),n,int(c or 1),int(o,16)) for a,w,n,c,o in re.findall(DECL,body)]
    raise AssertionError(structure)


def test_reference_inputs_match_pinned_manifests_and_extracted_svd():
    for item in json.loads((REF/'manifest.json').read_text()):
        assert hashlib.sha256((REF/item['path']).read_bytes()).hexdigest()==item['sha256']
    pack=json.loads((REF/'pack-manifest.json').read_text())
    archive=REF/Path(pack['url']).name
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==pack['sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.read('03_SVD/'+SVD.name)==SVD.read_bytes()


def test_physical_memory_and_interrupt_profile_match_device_definitions():
    root=ET.parse(REF/'TexasInstruments.MSPM0L11XX_L13XX_DFP.pdsc').getroot()
    device=next(d for d in root.findall('.//device') if d.get('Dname')==PROFILE['name'])
    memory={m.get('name'):(int(m.get('start'),0),int(m.get('size'),0)) for m in device.findall('memory')}
    assert memory['IROM1']==(0,PROFILE['flash_bytes'])
    for name,prefix in [('IRAM1','sram'),('NonMain','nonmain'),('Factory','factory')]:
        assert memory[name]==(PROFILE[prefix+'_base'],PROFILE[prefix+'_bytes'])
    regions=sorted((start,start+size) for start,size in memory.values())
    assert all(end<=next_start for (_,end),(next_start,_) in zip(regions,regions[1:]))
    macros={n:int(v,16) for n,v in re.findall(r'#define\s+(__\w+)\s+(0x[0-9A-Fa-f]+)U',DEVICE)}
    assert PROFILE['nvic_priority_bits']==macros['__NVIC_PRIO_BITS']
    assert PROFILE['mpu']==bool(macros['__MPU_PRESENT'])
    assert PROFILE['vtor']==bool(macros['__VTOR_PRESENT'])
    interrupts={name:int(number) for name,number in re.findall(r'(\w+)_INT_IRQn\s*=\s*(\d+)',DEVICE)}
    assert IRQ==interrupts
    # Highest external IRQ fits the actual NVIC bank; shared IRQs remain shared.
    assert max(IRQ.values())<32 and len(set(IRQ.values()))<len(IRQ)


@pytest.mark.parametrize('peripheral,header,prefix,groups',[
    *( (p,'hw_gptimer.h','GPTIMER',('CPU_INT','GEN_EVENT0','GEN_EVENT1')) for p in ['TIMG0','TIMG1','TIMG2','TIMG4'] ),
    ('DMA','hw_dma.h','DMA',('CPU_INT','GEN_EVENT')),
    ('COMP0','hw_comp.h','COMP',('CPU_INT','GEN_EVENT')),
])
def test_interrupt_block_arrays_follow_header_offsets_not_occupied_span(peripheral,header,prefix,groups):
    metadata=registers();addresses=[]
    for group in groups:
        for access,width,name,count,offset in fields(header,f'{prefix}_{group}_Regs'):
            assert count==1
            address=BASES[peripheral]+offset;register=metadata[address]
            assert register.name==peripheral+'_'+name
            assert (register.access,register.width)==(access,width)
            addresses.append(address)
    # Reserved word after each block must not become the next IIDX register.
    for group in groups:
        members=fields(header,f'{prefix}_{group}_Regs')
        last=max(offset+width//8 for _,width,_,_,offset in members)
        assert BASES[peripheral]+last not in metadata
    assert len(addresses)==len(set(addresses))


def test_adc_svt_relocation_and_ull_aliases_agree_with_independent_header():
    metadata=registers();svd=ET.parse(SVD).getroot()
    svt=next(p for p in svd.findall('peripherals/peripheral') if p.findtext('name')=='ADC0_SVT')
    svt_members=fields('hw_adc12.h','ADC12_SVTMEM_Regs')
    ull_members=fields('hw_adc12.h','ADC12_ULLMEM_Regs')
    for access,width,name,count,offset in svt_members:
        # Header covers a superset of silicon; the device SVD limits result count.
        original=next(r for r in svt.findall('.//register') if r.findtext('name').split('_')[-1].split('[')[0]==name)
        implemented=int(original.findtext('dim','1'),0)
        assert implemented<=count
        for index in range(implemented):
            address=BASES['ADC0_PERIPHERALREGIONSVT']+offset+index*width//8
            reg=metadata[address]
            assert (reg.access,reg.width)==(access,width)
            wrong=int(svt.findtext('baseAddress'),0)+int(original.findtext('addressOffset'),0)+index*width//8
            assert wrong not in metadata  # no double-counted SVT relocation
            if name=='MEMRES':
                ull=next(row for row in ull_members if row[2]==name)
                alias=metadata[BASES['ADC0']+ull[4]+index*width//8]
                assert (alias.width,alias.access,alias.reset,alias.mask)==(reg.width,reg.access,reg.reset,reg.mask)


def test_register_intervals_masks_resets_and_access_are_self_consistent():
    metadata=registers();occupied=set()
    accesses={'read-only','write-only','read-write','read-writeonce','writeOnce'}
    for address,reg in metadata.items():
        assert address==reg.address and reg.width in (8,16,32)
        assert address%(reg.width//8)==0 and reg.access in accesses
        interval=set(range(address,address+reg.width//8))
        assert not occupied&interval,(hex(address),reg.name)
        occupied|=interval
        assert 0<reg.mask<1<<reg.width and 0<=reg.reset<1<<reg.width
        assert not reg.reset&~reg.mask,(reg.name,reg.reset,reg.mask)
    # SVD's byte-wide secure event ports must remain byte-wide metadata, even
    # though that unsupported peripheral is not yet executable in the model.
    byte_ports=[r for r in metadata.values() if r.width==8]
    assert byte_ports and all(r.peripheral=='EVENTLP' for r in byte_ports)


def test_device_field_masks_do_not_exceed_family_header_bit_definitions():
    svd=ET.parse(SVD).getroot();covered=set()
    for peripheral in svd.findall('peripherals/peripheral'):
        name=peripheral.findtext('name');type_name=TYPES.get('ADC0_PERIPHERALREGIONSVT' if name=='ADC0_SVT' else name)
        if not type_name:continue  # EVENTLP is absent from the pinned device headers.
        path='hw_'+type_name.lower().split('_')[0]+'.h'
        if name=='SYSCTL':path='hw_sysctl_mspm0l11xx_l13xx.h'
        text=(REF/path).read_text()
        masks={n:int(v,16) for n,v in re.findall(r'#define\s+(\w+)_MASK\s+\(\(uint32_t\)(0x[0-9A-Fa-f]+)U\)',text)}
        for reg in peripheral.findall('.//register'):
            register=reg.findtext('name')[len(name)+1:].split('[')[0]
            for field in reg.findall('fields/field'):
                suffix='_'+register+'_'+field.findtext('name')
                candidates=[value for key,value in masks.items() if key.endswith(suffix)]
                if not candidates:continue
                device_mask=((1<<int(field.findtext('bitWidth'),0))-1)<<int(field.findtext('bitOffset'),0)
                # Family headers intentionally include wider timers/banks than
                # this device. The device may narrow a field, never expand it.
                assert any(device_mask&~candidate==0 for candidate in candidates),(name,register,suffix)
                covered.add(name)
    assert {'ADC0','ADC0_SVT','GPIOA','FLASHCTL','DMA','I2C0','I2C1','TIMG0','TIMG1','TIMG2','TIMG4','WWDT0','UART0','UART1'}<=covered
