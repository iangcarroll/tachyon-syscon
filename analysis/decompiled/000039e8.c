/* UNREVIEWED Ghidra output: FUN_000039e8 @ 000039e8 */

longlong FUN_000039e8(uint param_1,char *param_2,undefined4 param_3)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  
  iVar2 = DAT_00003a7c;
  uStack_1c = param_2;
  uStack_18 = param_3;
  if (*DAT_00003a78 == '\0') {
    iVar1 = FUN_000098dc(DAT_00003a7c,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x9b,DAT_00003a80);
  }
  iVar2 = DAT_00003a7c;
  if (0xf < param_1) {
    iVar1 = FUN_000098dc(DAT_00003a7c,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x9c,PTR_s_pin_<_IO_EXPANDER_TOTAL_PINS_00003a84);
  }
  uVar4 = param_1 >> 3;
  FUN_000036bc(uVar4 + 6,(int)&uStack_1c + 2);
  uVar3 = 1 << (param_1 & 7) & 0xff;
  if (((uint)uStack_1c >> 0x10 & 0xff & uVar3) == 0) {
    uVar4 = uVar4 + 2;
  }
  FUN_000036bc(uVar4,(int)&uStack_1c + 3);
  *param_2 = '\x01' - ((uVar3 & (uint)uStack_1c >> 0x18) == 0);
  return (ulonglong)param_1 << 0x20;
}


