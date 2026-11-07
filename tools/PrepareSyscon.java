// Ghidra pre-script for the pinned MSPM0 Cortex-M image. No hardware access.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.SourceType;
import java.math.BigInteger;

public class PrepareSyscon extends GhidraScript {
    public void run() throws Exception {
        MemoryBlock ram = currentProgram.getMemory().createUninitializedBlock("SRAM", toAddr(0x20000000L), 0x1000, false);
        ram.setRead(true); ram.setWrite(true); ram.setExecute(false);
        currentProgram.getProgramContext().setValue(currentProgram.getRegister("TMode"), toAddr(0), toAddr(0xf7fe), BigInteger.ONE);
        for (int i = 1; i < 48; i++) {
            long ptr = Integer.toUnsignedLong(getInt(toAddr(i * 4)));
            if ((ptr & 1) == 1 && ptr < 0xacc0) {
                var address = toAddr(ptr & ~1L);
                disassemble(address);
                if (getFunctionAt(address) == null) createFunction(address, i == 1 ? "Reset_Handler" : "vector_" + i);
                currentProgram.getSymbolTable().addExternalEntryPoint(address);
            }
        }
    }
}
