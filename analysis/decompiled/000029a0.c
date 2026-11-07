/* UNREVIEWED Ghidra output: FUN_000029a0 @ 000029a0 */

int FUN_000029a0(char *param_1,uint param_2,int param_3,int param_4,undefined4 *param_5)

{
  undefined1 *puVar1;
  int iVar2;
  int iVar3;
  char *pcVar4;
  char *pcVar5;
  uint uVar6;
  char *pcVar7;
  int local_3c;
  undefined1 auStack_38 [36];
  
  local_3c = 0;
  if (param_3 != 0) {
    local_3c = FUN_00002650(param_3);
  }
  param_2 = param_2 >> 6;
  FUN_000079d0();
  iVar3 = DAT_00002ab4;
  if (param_4 == 0) {
    pcVar7 = param_1;
    do {
      pcVar4 = pcVar7 + 0x40;
      pcVar5 = pcVar7;
      while (*pcVar5 == -1) {
        pcVar5 = pcVar5 + 1;
        if (pcVar5 == pcVar4) {
          *param_5 = pcVar7;
          return 1;
        }
      }
      pcVar7 = pcVar4;
    } while (param_1 + param_2 * 0x40 != pcVar4);
  }
  else if (param_4 == 1) {
    if ((param_3 == 0) || (local_3c == 0)) {
      iVar2 = FUN_000098dc(DAT_00002ab4,0x2f);
      if (iVar2 != 0) {
        iVar3 = FUN_000098dc(iVar3,0x2f);
        iVar3 = iVar3 + 1;
      }
      FUN_00002678(iVar3,0x174,DAT_00002ab8);
    }
    else {
      do {
        param_2 = param_2 - 1;
        pcVar7 = param_1 + param_2 * 0x40;
        FUN_0000976c(auStack_38,0x20,DAT_00002aa8,param_2);
        FUN_00002840(pcVar7);
        uVar6 = 0;
        while( true ) {
          if (local_3c + 1U <= uVar6) {
            *param_5 = pcVar7;
            return 1;
          }
          if (pcVar7[uVar6] != *(char *)(param_3 + uVar6)) break;
          uVar6 = uVar6 + 1;
        }
      } while (param_2 != 0);
    }
  }
  else {
    uVar6 = FUN_000096aa(param_3);
    if (uVar6 < param_2) {
      param_1 = param_1 + uVar6 * 0x40;
      iVar3 = FUN_00002840(param_1);
      if (iVar3 != 0) {
        FUN_000098b4(param_3,param_1,0x20);
        *(undefined1 *)(param_3 + 0x1e) = 0;
        puVar1 = (undefined1 *)FUN_00009828(param_3,0x3b);
        if (puVar1 != (undefined1 *)0x0) {
          *puVar1 = 0;
        }
        *param_5 = param_1;
        return iVar3;
      }
    }
    else {
      FUN_00008f88(1,DAT_00002ab0,DAT_00002aac);
    }
  }
  return 0;
}


