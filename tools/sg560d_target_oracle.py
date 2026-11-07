"""Original ARM ABI SG560D comparison with explicit external driver ports."""
from pathlib import Path
import struct
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R1
import build_runtime_scan_image as runtime
ENTRIES={0x5e30:'uart_stop',0x5f30:'power_check',0x614c:'uart_start',0x61b8:'fct_complete',0x61d0:'volume_release',0x61f0:'usbboot_release',0x6210:'powerkey_release_task',0x6230:'action_6230',0x6238:'action_6238',0x6240:'action_6240',0x6248:'pins_off',0x6282:'pins_on',0x62ec:'retry_delay',0x6384:'retry_schedule',0x6428:'poweron',0x64a0:'edl',0x6520:'special_boot',0x65d0:'fct',0x65da:'fct_callback',0x65e4:'fastboot',0x65f0:'wake_schedule',0x6650:'wake_remaining',0x6690:'off',0x66a0:'mode_name',0x66bc:'set_mode',0x6720:'poweroff',0x6838:'prepare_special',0x68a4:'prepare_edl',0x68fc:'prepare_normal',0x6948:'init',0x6a28:'key_assert',0x6a48:'key_release',0x6a68:'poll',0x7468:'key_pulse',0x7488:'action_7488',0x74a8:'action_74a8',0x74c8:'action_74c8',0x74e8:'raw_send'}
VOID={0x5e30,0x614c,0x6248,0x6282,0x6384,0x65f0,0x6a28,0x6a48,0x6a68}
# address -> (target symbol, explicit argument count). Return64 declarations are
# handled separately, because original Oracle hooks otherwise only set R0.
DEPENDENCIES={
0x2678:('syscon_target_assert',3),0x3114:('syscon_target_auto_boot',0),0x3150:('syscon_target_modem_always_on',0),0x3194:('syscon_target_hwrevision_new',0),
0x364e:('syscon_target_pin_write',2),0x386c:('syscon_target_ioexpander_configure',1),0x49d0:('syscon_target_protocol_poll',1),
0x4c50:('syscon_target_power_measure',1),0x4ca8:('syscon_target_power_battery_route',0),0x4d9c:('syscon_target_power_header_route',0),0x4e34:('syscon_target_power_battery_route_set',1),0x4ed4:('syscon_target_power_boost_set',1),0x4ee0:('syscon_target_power_header_route_set',1),0x4fd0:('syscon_target_power_header_default',0),0x5048:('syscon_target_power_vbus_route_set',1),0x517c:('syscon_target_power_shutdown_busy',0),0x5274:('syscon_target_power_battery_detect',0),0x5358:('syscon_target_power_report',1),
0x559c:('syscon_target_power_minimum_update',0),0x55b4:('syscon_target_power_minimum_reset',0),0x55c4:('syscon_target_power_minimum',0),0x55dc:('syscon_target_shutdown_set',1),0x562c:('syscon_target_shutdown_reason',0),0x5638:('syscon_target_shutdown_elapsed',0),0x5670:('syscon_target_shutdown_stale',0),0x567c:('syscon_target_shutdown_active',0),0x5694:('syscon_target_shutdown_poll',0),
0x591c:('syscon_target_powerkey_mode',1),0x5aa8:('syscon_target_retained_set_modem',1),0x5c68:('syscon_target_rgb_preset',2),0x5dbc:('syscon_target_rgb_state',0),0x7554:('syscon_target_tasks_submit',2),0x76d8:('syscon_target_tasks_active',0),0x77b4:('syscon_target_now',0),0x77c0:('syscon_target_timer_delay',1),0x7928:('syscon_target_wakeup_enable',1),0x7d54:('syscon_target_adc_temperature',0),0x7f58:('syscon_target_gpio_config',1),0x8054:('syscon_target_gpio_write',2),0x80f8:('syscon_target_gpio_read',1),0x8954:('syscon_target_uart_init',1),0x8b50:('syscon_target_uart_deinit',1),0x8c8c:('syscon_target_uart_write_buffer',3),
0x312c:('syscon_target_color',0),0x3af4:('syscon_target_uart_write',2)}
PAYLOADS={0x386c:3,0x7f58:12,0x8954:9}
RET64={0x77b4,0x5638,0x4e34,0x4ee0,0x5048}

def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    traps=destination/'sg_ports.S'
    names=[x[0] for x in DEPENDENCIES.values()]
    traps.write_text('.syntax unified\n.thumb\n'+''.join(f'.global {n}\n.type {n},%function\n.thumb_func\n{n}:\n bkpt #0\n bx lr\n' for n in names))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=old+['src/format.c','target/logger_target.c','target/logger_target_abi.S','target/hal_helpers.c','target/sg560d_target.c',str(traps)]
        return runtime.build(destination)
    finally:runtime.SOURCES=old

class AssertionBoundary(Exception):
    """Stop at the explicit fatal assertion endpoint, before board reset."""

class Pair:
    owners=None
    def __init__(self,elf,respond=None,logging=True):
        if self.owners is not None:self.owners.append(self)
        self.cpus=[Oracle(),ArmRebuildOracle(elf)];self.events=[[],[]]
        self.respond=respond or (lambda address,args:0);self.terminal_assert=False
        self.pointer_map={self.cpus[1].symbols['syscon_target_modem_'+name]|1:entry|1 for entry,name in ENTRIES.items()}
        self.pointer_map[self.cpus[1].symbols['syscon_target_mfg_logger']|1]=0x8fa1
        for i,cpu in enumerate(self.cpus):
            def state_write(uc,access,address,size,value,user,i=i):self.events[i].append(('state-write',address,size,value&((1<<(size*8))-1)))
            cpu.cpu.hook_add(UC_HOOK_MEM_WRITE,state_write,begin=0x20000000,end=0x200007ff)
            for address,(symbol,count) in DEPENDENCIES.items():
                target=address if i==0 else cpu.symbols[symbol]&~1
                cpu.hooks[target]=lambda o,i=i,address=address,count=count:self.dependency(i,address,count)
        self.put(0x2000080c,bytes([logging]))
    def put(self,address,data):
        for cpu in self.cpus:cpu.put(address,data)
    def dependency(self,index,address,count):
        cpu=self.cpus[index];args=tuple(cpu.arg(i) for i in range(count));data=b''
        if address in PAYLOADS:data=bytes(cpu.cpu.mem_read(cpu.arg(1),PAYLOADS[address]))
        elif address==0x7554:
            args=(cpu.arg(1),);data=bytearray(cpu.cpu.mem_read(cpu.arg(0),args[0]*8))
            if index:
                for offset in range(0,len(data),8):
                    if not data[offset]:
                        value=struct.unpack_from('<I',data,offset+4)[0]
                        assert value in self.pointer_map,hex(value)
                        struct.pack_into('<I',data,offset+4,self.pointer_map[value])
            data=bytes(data)
        elif address==0x5358 and index:args=(self.pointer_map[cpu.arg(0)],)
        elif address==0x3af4:
            pointer,size=(cpu.arg(0),cpu.arg(1)) if index==0 else (cpu.arg(1),cpu.arg(2))
            args=(0,);data=bytes(cpu.cpu.mem_read(pointer,size))
        elif address==0x8c8c:
            args=(cpu.arg(0),);data=bytes(cpu.cpu.mem_read(cpu.arg(1),cpu.arg(2)))
        self.events[index].append((address,args,data))
        if address==0x2678 and self.terminal_assert:raise AssertionBoundary
        result=self.respond(address,args)
        if address in RET64:cpu.cpu.reg_write(UC_ARM_REG_R1,(result>>32)&0xffffffff)
        return result if index else result&0xffffffff
    def call(self,entry,*args,check_return=None):
        self.active_cpu=0
        expected=self.cpus[0].call(entry,*args,count=2000000)
        self.active_cpu=1
        actual=self.cpus[1].call('syscon_target_modem_'+ENTRIES[entry],*args,count=2000000)
        if check_return is None:check_return=entry not in VOID
        if check_return:assert actual==expected,(hex(entry),args,actual,expected)
        assert bytes(self.cpus[0].cpu.mem_read(0x20000000,0x800))==self.cpus[1].read(0x20000000,0x800),(hex(entry),'state')
        
        if self.events[0]!=self.events[1]:
            from itertools import zip_longest
            mismatch=next((n,a,b) for n,(a,b) in enumerate(zip_longest(*self.events)) if a!=b)
            raise AssertionError((hex(entry),mismatch))
        return actual
