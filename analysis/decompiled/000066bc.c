/* UNREVIEWED Ghidra output: FUN_000066bc @ 000066bc */

/* WARNING: Function: __gnu_thumb1_case_uqi replaced with injection: switch8_r0 */
/* WARNING (jumptable): Removing unreachable block (ram,0x000066e2) */
/* WARNING: Removing unreachable block (ram,0x000066e2) */

undefined4 FUN_000066bc(undefined4 param_1)

{
  undefined4 uVar1;
  
  uVar1 = FUN_000066a0();
  FUN_00008f88(3,DAT_00006718,DAT_00006714,uVar1);
  *DAT_0000671c = (char)param_1;
  FUN_00005aa8(param_1);
  switch(param_1) {
  case 1:
    uVar1 = 0;
    break;
  case 2:
    uVar1 = 4;
    goto LAB_000066ee;
  case 3:
    uVar1 = 1;
    break;
  case 4:
    uVar1 = 2;
    break;
  case 5:
    uVar1 = 3;
LAB_000066ee:
    FUN_00005c68(uVar1);
switchD_000066e2_default:
    uVar1 = 0;
    goto LAB_000066fe;
  default:
    goto switchD_000066e2_default;
  }
  FUN_00005c68(uVar1);
  uVar1 = 1;
LAB_000066fe:
  FUN_0000591c(uVar1);
  return 0;
}


