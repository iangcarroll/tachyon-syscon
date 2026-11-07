/* UNREVIEWED Ghidra output: FUN_000066a0 @ 000066a0 */

undefined4 FUN_000066a0(char param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_000066b4;
  if ((byte)(param_1 - 1) < 5) {
    uVar1 = *(undefined4 *)((uint)(byte)(param_1 - 1) * 4 + DAT_000066b8);
  }
  return uVar1;
}


