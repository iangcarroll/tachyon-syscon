/* UNREVIEWED Ghidra output: FUN_00006650 @ 00006650 */

/* WARNING: Removing unreachable block (ram,0x0000666c) */

undefined4 FUN_00006650(void)

{
  uint uVar1;
  undefined4 uVar2;
  ulonglong uVar3;
  
  uVar3 = FUN_000077b4();
  uVar1 = (uint)*DAT_0000668c;
  if (uVar1 == 0 && *(int *)((int)DAT_0000668c + 4) == 0) {
    uVar2 = 0xffffffff;
  }
  else if (uVar3 < *DAT_0000668c) {
    uVar2 = FUN_00000448(uVar1 - (uint)uVar3,
                         (*(int *)((int)DAT_0000668c + 4) - (int)(uVar3 >> 0x20)) -
                         (uint)(uVar1 < (uint)uVar3),1000,0);
  }
  else {
    uVar2 = 0;
  }
  return uVar2;
}


