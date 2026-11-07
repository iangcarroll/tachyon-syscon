/* UNREVIEWED Ghidra output: FUN_00005c68 @ 00005c68 */

undefined4 FUN_00005c68(uint param_1,undefined4 param_2)

{
  undefined1 uVar1;
  undefined1 *puVar2;
  undefined4 uVar3;
  
  puVar2 = DAT_00005ca0;
  if (param_1 < 10) {
    uVar1 = *DAT_00005c9c;
    *DAT_00005c9c = (char)param_1;
    *puVar2 = uVar1;
    uVar3 = FUN_000000e8(param_2,0x14);
    *DAT_00005ca4 = uVar3;
    uVar3 = FUN_00005c38(DAT_00005ca8 + param_1 * 5);
  }
  else {
    uVar3 = 0xffffffff;
  }
  return uVar3;
}


