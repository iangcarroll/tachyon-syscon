import ctypes as C
import random
import struct
from oracle import Oracle

CALL=C.CFUNCTYPE(C.c_uint32,C.c_void_p,*([C.c_uint32]*5))
ARG_COUNTS={0x80f8:1,0x7880:1,0x81f8:1,0x781c:4,0x6a28:0,
            0x6a48:0,0x8148:4,0x6690:0,0x315c:0,0x3178:0,
            0x8f88:4,0x10021:2}

class KeyPair:
    def __init__(self,lib):
        self.lib=lib;self.o=Oracle();self.state=C.create_string_buffer(64)
        self.events=[];self.native_events=[]
        self.high=0;self.active=0;self.seconds=3;self.mutation=None
        for address,count in ARG_COUNTS.items():
            def hook(o,address=address,count=count):
                args=[o.arg(i) for i in range(count)]
                self.events.append((address,*args))
                if address==0x10021 and self.mutation is not None:
                    offset,data=self.mutation
                    original=0x200000b4+offset if offset<40 else 0x20000390+offset-40
                    self.o.put(original,data)
                return self.result(address)
            self.o.hooks[address&~1]=hook
        def native(_,address,a,b,c,d):
            self.native_events.append((address,*[a,b,c,d][:ARG_COUNTS[address]]))
            if address==0x10021 and self.mutation is not None:
                offset,data=self.mutation
                C.memmove(C.addressof(self.state)+offset,data,len(data))
            return self.result(address)
        self.cb=CALL(native)
        self.state.raw=self.original_state()
        for name in ['poll','debounce']:
            getattr(lib,'syscon_key_'+name).argtypes=[C.c_void_p,CALL,C.c_void_p]
        for name in ['edge','mode']:
            getattr(lib,'syscon_key_'+name).argtypes=[C.c_void_p,C.c_uint32,CALL,C.c_void_p]
        lib.syscon_key_register.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32]

    def result(self,address):
        return {0x80f8:self.high,0x6690:self.active,0x315c:self.seconds,
                0x3178:self.seconds}.get(address,0)

    def original_state(self):
        return bytes(self.o.cpu.mem_read(0x200000b4,40))+bytes(self.o.cpu.mem_read(0x20000390,24))

    def seed(self,data):
        self.state.raw=data
        self.o.put(0x200000b4,data[:40]);self.o.put(0x20000390,data[40:])

    def step(self,name,*args):
        self.events.clear();self.native_events.clear()
        addresses=dict(edge=0x570c,poll=0x5740,debounce=0x5844,register=0x5908,mode=0x591c)
        self.o.call(addresses[name],*args)
        fn=getattr(self.lib,'syscon_key_'+name)
        if name=='register': assert fn(self.state,*args)==0
        else: fn(self.state,*args,self.cb,None)
        assert self.state.raw==self.original_state(),(name,args,self.state.raw.hex(),self.original_state().hex())
        assert self.native_events==self.events,(name,args,self.native_events[-12:],self.events[-12:])


def test_power_key_press_release_sessions(lib):
    p=KeyPair(lib)
    for mode in [0,1,2,256,0xffffffff]:
        for seconds in [3,7,30]:
            for duration in [0,4,5,299,300,599,600,799,800,3100]:
                p.step('mode',mode)
                p.step('register',0x10021,0x12345678)
                p.seconds=seconds;p.active=seconds&1;p.high=0
                p.step('edge',0);p.step('debounce')
                for _ in range(duration): p.step('poll')
                p.high=1
                for _ in range(22): p.step('poll')


def test_power_key_random_state_boundaries_and_callback_mutation(lib):
    p=KeyPair(lib);rng=random.Random(0x5740)
    counters=[0,40,49,50,199,200,201,2999,5990,5999,6000,7999,0xfffffff5,0xffffffff]
    for index in range(500):
        data=bytearray(rng.randbytes(64))
        # Exercise legal and irregular threshold tables, including overlap and wrap.
        for i in range(3): struct.pack_into('<III',data,i*12,rng.choice(counters),rng.choice(counters),rng.getrandbits(32))
        data[36]=rng.choice([0,1,2,255]);data[37]=rng.choice([0,2,4,254,255])
        struct.pack_into('<III',data,40,rng.choice(counters),rng.choice([0,0x10021]),rng.choice(counters))
        data[52]=rng.choice([0,1,255]);data[53]=rng.choice([0,1,255])
        p.seed(bytes(data));p.high=rng.choice([0,1,7]);p.active=rng.randrange(2)
        p.seconds=rng.choice([0,3,30,0xffffffff])
        p.mutation=rng.choice([None,(36,b'\0'),(52,b'\0'),(37,b'\x02')])
        p.step('poll')
        p.step('debounce')
        p.step('edge',rng.getrandbits(32))


def test_power_key_initialization_configuration_and_order(lib):
    CONFIG=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_void_p)
    lib.syscon_key_init.argtypes=[C.c_void_p,C.c_uint32,CALL,CONFIG,C.c_void_p]
    for mode in [0,1,2,255,256,0xffffffff]:
        p=KeyPair(lib)
        p.o.hooks[0x7f58]=lambda o:p.events.append(('configure',o.arg(0),bytes(o.cpu.mem_read(o.arg(1),12))))
        p.o.hooks[0x776c]=lambda o:p.events.append(('timer_init',))
        base_call=p.cb
        cb=CALL(lambda ctx,address,a,b,c,d:p.native_events.append(('timer_init',)) or 0 if address==0x776c else base_call(ctx,address,a,b,c,d))
        config=CONFIG(lambda _,pin,data:p.native_events.append(('configure',pin,C.string_at(data,12))))
        assert p.o.call(0x5970,mode)==lib.syscon_key_init(p.state,mode,cb,config,None)==0
        assert p.native_events==p.events
        assert p.state.raw==p.original_state()
