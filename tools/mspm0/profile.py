"""Pinned TI SVD register metadata, with reviewed device-header corrections."""
from dataclasses import dataclass,replace
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
SVD=ROOT/'references/ti-mspm0/MSPM0L130X.svd'

@dataclass(frozen=True)
class Register:
    address:int
    peripheral:str
    name:str
    access:str
    reset:int
    mask:int
    width:int

def integer(text,default=0):return int(text,0) if text is not None else default

def registers():
    root=ET.parse(SVD).getroot();result={}
    def walk(node,offset,peripheral):
        for item in node:
            if item.tag not in ('register','cluster'):continue
            start=offset+integer(item.findtext('addressOffset'))
            count=integer(item.findtext('dim'),1);step=integer(item.findtext('dimIncrement'))
            # DFP1.3.1 mistakenly uses the 44-byte occupied register span as
            # the array stride. TI GPTIMER/DMA/COMP headers place successive
            # CPU/GEN event blocks at0x1020,0x1050,0x1080 (48-byte stride).
            if (item.tag=='cluster' and item.findtext('name')==f'{peripheral}_INT_EVENT[%s]'
                    and peripheral in {'TIMG0','TIMG1','TIMG2','TIMG4','DMA','COMP0'}):
                if step!=44 or count not in (2,3):
                    raise ValueError(f'Unexpected interrupt cluster layout for {peripheral}')
                step=48
            for index in range(count):
                address=start+index*step
                if item.tag=='cluster':walk(item,address,peripheral);continue
                width=integer(item.findtext('size'),32)
                name=item.findtext('name').replace('%s',str(index))
                mask=0
                for field in item.findall('fields/field'):
                    field_width=integer(field.findtext('bitWidth'));bit=integer(field.findtext('bitOffset'))
                    mask|=((1<<field_width)-1)<<bit
                reg=Register(address,peripheral,name,item.findtext('access','read-write'),
                             integer(item.findtext('resetValue')),mask or ((1<<width)-1),width)
                assert address not in result,hex(address)
                result[address]=reg
    for peripheral in root.findall('peripherals/peripheral'):
        name=peripheral.findtext('name');base=integer(peripheral.findtext('baseAddress'))
        # TI pack double-counts the ADC SVT relocation: offsets are relative to
        # ADC0 (0x40004000), despite declaring the relocated base0x4055a000.
        # Header ADC12_PERIPHERALREGIONSVT_Regs offsets0x160/0x280 and datasheet
        # peripheral map independently establish the corrected final addresses.
        if name=='ADC0_SVT':base=0x40004000
        children=peripheral.find('registers')
        walk(children if children is not None else [],base,name)
    # The pack omits the ULL view of the same four conversion results. The
    # device header declares MEMRES at ADC0+0x1280, also used by this image.
    for index in range(4):
        alias=result[0x4055a280+4*index]
        address=0x40005280+4*index
        assert address not in result
        result[address]=replace(alias,address=address,peripheral='ADC0',name=f'ADC0_MEMRES[{index}]')
    return result

# SVD CPU metadata incorrectly says MPU present and 3 priority bits. The pinned
# device header says no MPU, VTOR present and 2 bits; these overrides are explicit.
PROFILE=dict(name='MSPM0L1306',part_confirmed=False,core='Cortex-M0+',
    unicorn_cpu='Cortex-M0 ARMv6-M',flash_bytes=65536,flash_cpu_limit=65528,
    sram_base=0x20000000,sram_bytes=4096,nonmain_base=0x41c00000,nonmain_bytes=512,
    factory_base=0x41c40000,factory_bytes=128,nvic_priority_bits=2,mpu=False,vtor=True,
    main_alias=0x00400000,nonmain_alias=0x41c10000,factory_alias=0x41c50000)

IRQ={'WWDT0':0,'FLASHCTL':0,'DEBUGSS':0,'SYSCTL':0,'GPIOA':1,'COMP0':1,'TIMG1':2,'ADC0':4,
     'SPI0':9,'UART1':13,'UART0':15,'TIMG0':16,'TIMG2':18,'TIMG4':20,
     'I2C0':24,'I2C1':25,'DMA':31}
