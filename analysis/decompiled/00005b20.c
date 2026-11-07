/* UNREVIEWED Ghidra output: FUN_00005b20 @ 00005b20 */

byte FUN_00005b20(int param_1)

{
  int iVar1;
  byte bVar2;
  
  iVar1 = DAT_00005b44;
  bVar2 = FUN_000004e4(*(undefined4 *)(DAT_00005b44 + 8));
  bVar2 = FUN_000000e8(param_1 * (uint)bVar2,100);
  if (*(char *)(iVar1 + 0x10) == '\0') {
    bVar2 = ~bVar2;
  }
  return bVar2;
}


