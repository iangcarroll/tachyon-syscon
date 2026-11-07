// Export machine-generated analysis. Decompiled C is NOT a verified reconstruction.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import java.io.*;

public class ExportSyscon extends GhidraScript {
    public void run() throws Exception {
        File out = new File(getScriptArgs()[0]); out.mkdirs();
        File funcs = new File(out, "decompiled"); funcs.mkdirs();
        DecompInterface decompiler = new DecompInterface(); decompiler.openProgram(currentProgram);
        try (PrintWriter index = new PrintWriter(new File(out, "functions.tsv"));
             PrintWriter listing = new PrintWriter(new File(out, "listing.txt"));
             PrintWriter refs = new PrintWriter(new File(out, "references.tsv"));
             PrintWriter ranges = new PrintWriter(new File(out, "function-ranges.tsv"))) {
            index.println("address\tname\tbytes\tdecompiled");
            refs.println("function\tfrom\tto\ttype");
            ranges.println("function\tstart\tend_inclusive");
            for (var f : currentProgram.getFunctionManager().getFunctions(true)) {
                var r = decompiler.decompileFunction(f, 30, monitor);
                String addr = f.getEntryPoint().toString();
                index.printf("%s\t%s\t%d\t%b%n", addr, f.getName(), f.getBody().getNumAddresses(), r.decompileCompleted());
                for (var range : f.getBody().getAddressRanges())
                    ranges.printf("%s\t%s\t%s%n",addr,range.getMinAddress(),range.getMaxAddress());
                try (PrintWriter c = new PrintWriter(new File(funcs, addr + ".c"))) {
                    c.println("/* UNREVIEWED Ghidra output: " + f.getName() + " @ " + addr + " */");
                    c.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : r.getErrorMessage());
                }
            }
            for (var ins : currentProgram.getListing().getInstructions(true)) {
                listing.printf("%s  %s%n", ins.getAddress(), ins.toString());
                var f = getFunctionContaining(ins.getAddress());
                for(var ref : ins.getReferencesFrom())
                    refs.printf("%s\t%s\t%s\t%s%n", f == null ? "?" : f.getEntryPoint().toString(),ins.getAddress(),ref.getToAddress(),ref.getReferenceType());
            }
        }
        decompiler.dispose();
    }
}
