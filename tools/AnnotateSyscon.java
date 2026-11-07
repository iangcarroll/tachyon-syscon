import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.address.AddressSet;

public class AnnotateSyscon extends GhidraScript {
    public void run() throws Exception {
        // Independently referenced callbacks/constructors missed by direct-call
        // discovery. These were inspected as Thumb entrypoints, not assumed from
        // arbitrary numeric values in data. The references are retained in notes.
        long[] callbacks = {0x3a88,0x3ec0,0x50f4,0x570c,0x5740,0x5844,0x5cac,
            0x5edc,0x61b8,0x61d0,0x61f0,0x6230,0x6238,0x6240,0x74a8,0x74c8,
            0x78ac,0x8fa0,0x9012,0x9a20,0x9d24};
        for(long code : callbacks) {
            var target=toAddr(code); disassemble(target);
            if(getFunctionAt(target)==null) createFunction(target,null);
        }
        // Compiler ABI veneers independently identified and executed during
        // source-runtime reconstruction (runtime_arithmetic_mappings.py).
        long[] runtimeEntries={0x3d4,0x3dc,0x3f8,0x420,0x2354,0x2364,
            0x2374,0x2380,0x2394,0x23a8};
        for(long code:runtimeEntries) {
            var target=toAddr(code);disassemble(target);
            if(getFunctionAt(target)==null)createFunction(target,null);
        }
        for (long a = 0xc419; a < 0xc61f; a += 14) {
            long ptr = Integer.toUnsignedLong(getInt(toAddr(a)));
            StringBuilder s = new StringBuilder();
            for (int i = 0; getByte(toAddr(ptr+i)) != 0; i++) s.append((char)getByte(toAddr(ptr+i)));
            long code = Integer.toUnsignedLong(getInt(toAddr(a+4))) & ~1L;
            var target = toAddr(code); disassemble(target);
            var f = getFunctionAt(target);
            if (f == null) f = createFunction(target, null);
            if (f != null && f.getName().startsWith("FUN_")) f.setName("cmd_" + s.toString(), SourceType.USER_DEFINED);
        }
        for (long a=0xacc0; a<0xe2a0;) {
            long end=a;
            while(end<0xe2a0 && getByte(toAddr(end))>=32 && getByte(toAddr(end))<127) end++;
            if (end-a>=4 && getByte(toAddr(end))==0 && getDataContaining(toAddr(a))==null) {
                try { createAsciiString(toAddr(a)); } catch(Exception ignored) {}
            }
            a=end+1;
        }
        analyzeAll(currentProgram);
        // Differential execution reached the pointer-format branch omitted by
        // Ghidra's computed-switch recovery. These are observed instructions.
        disassemble(toAddr(0x9256));
        var formatter=getFunctionAt(toAddr(0x9038));
        if(formatter!=null) {
            var body=new AddressSet(formatter.getBody());
            body.addRange(toAddr(0x9256),toAddr(0x9269));
            formatter.setBody(body);
        }
        // Original float-divide execution reaches 0xbc0. Ghidra decoded
        // that computed-jump destination as ARM, despite this Cortex-M0+
        // image having only Thumb code. The table at0xabf4 and branches into
        // 0xae6 independently identify the omitted internal blocks.
        long[][] divideBlocks={{0xa94,0xab7},{0xae0,0xae1},{0xbc0,0xbf7}};
        for(long[] block:divideBlocks) {
            var start=toAddr(block[0]);var end=toAddr(block[1]);
            clearListing(start,end);
            currentProgram.getProgramContext().setValue(
                currentProgram.getRegister("TMode"),start,end,java.math.BigInteger.ONE);
            disassemble(start);
        }
        var divide=getFunctionAt(toAddr(0xa24));
        if(divide!=null) {
            var body=new AddressSet(divide.getBody());
            body.addRange(toAddr(0xa24),toAddr(0xc45));
            divide.setBody(body);
        }
        // The multiply switch table at0xac74 dispatches into blocks Ghidra
        // omitted from its body. The next entry is0x1000; final literals start
        // at0xff8. Source arithmetic tests execute these blocks independently.
        var multiply=getFunctionAt(toAddr(0xdb4));
        if(multiply!=null) {
            var body=new AddressSet(multiply.getBody());
            body.addRange(toAddr(0xdb4),toAddr(0xff7));
            multiply.setBody(body);
        }
    }
}
