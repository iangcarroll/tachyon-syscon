import ctypes as C
import random
import struct
from application_oracle import ApplicationOracle,DEPENDENCIES
from test_sg560d import DEPENDENCY,Environment


class Comparison:
    def __init__(self,lib,responses=None,initial=None):
        self.lib=lib;self.responses=responses or {};self.events=[]
        def response(fn,args):
            value=self.responses.get((fn,args),self.responses.get(fn,0))
            return value&0xffffffffffffffff
        self.response=response
        self.o=ApplicationOracle(response)
        if initial is not None:self.o.put(0x20000000,initial)
        self.state=C.create_string_buffer(bytes(self.o.cpu.mem_read(0x20000000,4096)),4096)
        def callback(_,fn,a,b,c,d,payload,length):
            if fn in (0x8954,0x7f58):args=(a,);data=C.string_at(payload,length)
            else:args=(a,b,c,d)[:DEPENDENCIES[fn]];data=b''
            self.events.append((fn,args,data));return response(fn,args)
        self.cb=DEPENDENCY(callback);self.env=Environment(self.cb,None)
        for name in ('constructors','init','tick'):
            getattr(lib,'syscon_application_'+name).argtypes=[C.c_void_p,C.POINTER(Environment)]
        lib.syscon_application_event.argtypes=[C.c_void_p,C.c_uint8]
        lib.syscon_application_helper.argtypes=[C.c_void_p,C.POINTER(Environment),C.c_uint32,C.c_uint32,C.c_uint32]
        lib.syscon_application_helper.restype=C.c_uint64
        lib.syscon_application_count.argtypes=[C.c_void_p,C.c_uint32]
        lib.syscon_application_count.restype=C.c_uint32

    def compare(self):
        assert self.state.raw[:0xf00]==bytes(self.o.cpu.mem_read(0x20000000,0xf00))
        assert self.events==self.o.events,(self.events,self.o.events)

    def constructors(self):
        self.o.call(0x96d4)
        self.lib.syscon_application_constructors(self.state,C.byref(self.env));self.compare()

    def init(self):
        self.o.run_init();self.lib.syscon_application_init(self.state,C.byref(self.env));self.compare()

    def tick(self):
        self.o.run_tick();self.lib.syscon_application_tick(self.state,C.byref(self.env));self.compare()

    def event(self,value):
        self.o.call(0x3a8c,value);self.lib.syscon_application_event(self.state,value);self.compare()


def test_application_constructor_order_and_ring_buffer_overflow(lib):
    rng=random.Random(0x3ec0)
    cmp=Comparison(lib,{0x77b4:0x123456789abcdef0},rng.randbytes(4096))
    cmp.constructors()
    C.memset(C.addressof(cmp.state)+0x2ec,0,1);cmp.o.put(0x200002ec,b'\0')
    for _ in range(10):
        for event in [0,1,2,3,4,5,255]:cmp.event(event)
        for _ in range(7):
            expected=cmp.o.call(0x3b0c,0x200002d8)
            assert lib.syscon_application_count(cmp.state,0x200002d8)==expected
            cmp.tick()


def test_application_init_reset_and_configuration_decisions(lib):
    for reset in range(8):
        for automatic in (0,1):
            for fct in (0,1):
                for mode in (1,2,5):
                    cmp=Comparison(lib,{0x7c08:reset,0x3114:automatic,0x3144:fct,
                        0x5ac4:mode,0x5af0:2,0x3808:-1,0x54cc:-1,0x6948:-1})
                    cmp.init()


def test_application_event_paths_deferred_shutdown_and_loop_order(lib):
    for event in range(8):
        for was_off in (0,1):
            for alternate in (0,1):
                for immediate in (0,1):
                    cmp=Comparison(lib,{0x3138:alternate,0x6690:was_off,0x51c0:immediate})
                    cmp.constructors()
                    C.memset(C.addressof(cmp.state)+0x2ed,was_off,1)
                    cmp.o.put(0x200002ed,bytes([was_off]))
                    cmp.event(event);cmp.tick();cmp.tick()
    for deferred in (0,1):
        for active in (0,1):
            cmp=Comparison(lib,{0x76d8:active,0x3144:1})
            cmp.constructors();cmp.event(1)
            C.memset(C.addressof(cmp.state)+0x2ec,deferred,1)
            cmp.o.put(0x200002ec,bytes([deferred]))
            cmp.tick()


def test_application_loop_helpers(lib):
    for entry in (0x3610,0x3ec0,0x3ad4,0x4c14,0x7974,0x3af4,0x7910):
        for result in (0,1):
            cmp=Comparison(lib,{0x51c0:result,0x77b4:0xffffffff})
            C.memset(C.addressof(cmp.state)+0x680,result,1)
            cmp.o.put(0x20000680,bytes([result]))
            cmp.o.hooks.pop(entry,None)
            cmp.o.call(entry,0x20000200,8)
            lib.syscon_application_helper(cmp.state,C.byref(cmp.env),entry,0x20000200,8)
            cmp.compare()


def test_wake_irq_enable_debounce_and_flag_consumption(lib):
    for requested in (0,1,255):
        for configured in (0,1):
            cmp=Comparison(lib,{0x3120:configured})
            cmp.o.call(0x7928,requested)
            lib.syscon_application_helper(cmp.state,C.byref(cmp.env),0x7928,requested,0)
            cmp.compare()
    for off in (0,1):
        for level in (0,1,2):
            for oldflag in (0,1,255):
                cmp=Comparison(lib,{0x6690:off,0x80f8:level})
                cmp.o.put(0x20000680,bytes([oldflag]));C.memset(C.addressof(cmp.state)+0x680,oldflag,1)
                cmp.o.call(0x78ac,17)
                lib.syscon_application_helper(cmp.state,C.byref(cmp.env),0x78ac,17,0)
                cmp.compare()
                cmp.o.hooks.pop(0x7974,None)
                cmp.o.call(0x7974)
                lib.syscon_application_helper(cmp.state,C.byref(cmp.env),0x7974,0,0)
                cmp.compare()


class ComposedComparison(Comparison):
    """Real C application + SG560D + scheduler; external hardware remains hooks."""
    def __init__(self,lib,responses):
        from sg560d_oracle import DEPENDENCIES as SG_DEPS,PAYLOADS
        from test_tasks import CALL
        super().__init__(lib,responses)
        self.signatures=dict(DEPENDENCIES);self.signatures.update(SG_DEPS)
        self.sg_entries={0x5e30,0x5f30,0x614c,0x61b8,0x61d0,0x61f0,0x6210,
            0x6230,0x6238,0x6240,0x6248,0x6282,0x62ec,0x6384,0x6428,0x64a0,
            0x6520,0x65d0,0x65da,0x65e4,0x65f0,0x6650,0x6690,0x66a0,0x66bc,
            0x6720,0x6838,0x68a4,0x68fc,0x6948,0x6a28,0x6a48,0x6a68,
            0x7468,0x7488,0x74a8,0x74c8}
        self.app_entries={0x4c14,0x7974}
        for fn,count in self.signatures.items():
            self.o.hooks[fn]=lambda o,fn=fn,count=count:self.o._dependency(fn,count)
        for fn,length in PAYLOADS.items():
            def payload_hook(o,fn=fn,length=length):
                args=(o.arg(0),);data=bytes(o.cpu.mem_read(o.arg(1),length))
                self.o.events.append((fn,args,data));return self.response(fn,args)&0xffffffff
            self.o.hooks[fn]=payload_hook
        for fn in self.sg_entries|self.app_entries|{0x7540,0x7554,0x75d8,0x76d8}:
            self.o.hooks.pop(fn,None)
        lib.sg560d_execute.argtypes=[C.c_void_p,C.POINTER(Environment),C.c_uint32,C.c_uint32,C.c_uint32]
        lib.sg560d_execute.restype=C.c_uint64
        lib.syscon_tasks_init.argtypes=[C.c_void_p]
        lib.syscon_tasks_submit.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
        lib.syscon_tasks_poll.argtypes=[C.c_void_p,C.c_uint64,CALL,C.c_void_p]
        lib.syscon_tasks_active.argtypes=[C.c_void_p]
        self.task_callback=CALL(lambda _,fn:lib.sg560d_execute(self.state,C.byref(self.env),fn&~1,0,0))
        def callback(_,fn,a,b,c,d,payload,length):
            if fn in self.sg_entries:return lib.sg560d_execute(self.state,C.byref(self.env),fn,a,b)
            if fn in self.app_entries:return lib.syscon_application_helper(self.state,C.byref(self.env),fn,a,b)
            tasks=C.addressof(self.state)+0x534
            if fn==0x7540:lib.syscon_tasks_init(tasks);return 0
            if fn==0x7554:return lib.syscon_tasks_submit(tasks,payload,b)&0xffffffff
            if fn==0x76d8:return lib.syscon_tasks_active(tasks)
            if fn==0x75d8:
                # This deterministic composition exercises one active task slot.
                # The scheduler C API accepts time explicitly; record the clock
                # read that the original performs for a delay action.
                active=[]
                for slot in range(2):
                    base=0x534+108*slot;data=self.state.raw
                    if data[base+104]:active.append(base)
                assert len(active)<=1
                for base in active:
                    data=self.state.raw;current=data[base+97]
                    if current<data[base+96] and data[base+current*8]==1:
                        self.events.append((0x77b4,(),b''))
                lib.syscon_tasks_poll(tasks,self.response(0x77b4,()),self.task_callback,None)
                return 0
            if fn in PAYLOADS:args=(a,);data=C.string_at(payload,length)
            else:args=(a,b,c,d)[:self.signatures[fn]];data=b''
            self.events.append((fn,args,data));return self.response(fn,args)
        self.cb=DEPENDENCY(callback);self.env=Environment(self.cb,None)


def test_composed_application_sg560d_and_scheduler_boot_then_shutdown(lib):
    responses={0x7c08:1,0x3114:1,0x3150:1,0x5274:1,0x3194:1,
        0x7d54:499,0x51c0:1,(0x4c50,(14,)):4000,(0x4c50,(16,)):4500}
    cmp=ComposedComparison(lib,responses)
    cmp.constructors();cmp.init()
    for time,voltage in [(1,0),(2,0),(2001,0),(2002,0),(2003,0),(2200,1700)]:
        responses[0x77b4]=time;responses[(0x4c50,(15,))]=voltage
        cmp.tick()
    assert cmp.state.raw[0x4f1]==2
    cmp.event(0);cmp.tick()  # Press captures the powered-on state.
    cmp.event(2);cmp.tick()  # Long press requests power-off with alternate mode off.
    assert cmp.state.raw[0x4f2]==3
    responses[0x77b4]=2300;responses[(0x4c50,(15,))]=0
    cmp.tick()
    assert cmp.state.raw[0x4f1:0x4f3]==b'\0\0'
