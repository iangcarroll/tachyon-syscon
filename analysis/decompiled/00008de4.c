/* UNREVIEWED Ghidra output: FUN_00008de4 @ 00008de4 */

uint FUN_00008de4(int param_1)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  
  iVar1 = FUN_00007ac0();
  iVar2 = DAT_00008e5c;
  if (iVar1 == 0) {
    iVar1 = FUN_000098dc(DAT_00008e5c,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0xde,DAT_00008e60);
  }
  if ((*(char *)(DAT_00008e64 + param_1 * 9 + 8) == '\0') &&
     (iVar2 = FUN_00008cf0(param_1), 0 < iVar2)) {
    FUN_0000891c(param_1);
    iVar2 = DAT_00008e68 + param_1 * 0x4c;
    uVar3 = (uint)*(byte *)(iVar2 + *(int *)(iVar2 + 0x44));
    *(uint *)(iVar2 + 0x44) = *(int *)(iVar2 + 0x44) + 1U & 0x3f;
    *(undefined1 *)(iVar2 + 0x48) = 0;
    FUN_00008938(param_1);
  }
  else {
    uVar3 = 0xffffffff;
  }
  return uVar3;
}


