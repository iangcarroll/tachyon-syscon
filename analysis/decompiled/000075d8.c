/* UNREVIEWED Ghidra output: FUN_000075d8 @ 000075d8 */

void FUN_000075d8(void)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  byte *pbVar4;
  int iVar5;
  undefined8 uVar6;
  
  iVar3 = 0;
  pbVar4 = DAT_000076b4;
  do {
    uVar2 = DAT_000076c0;
    if (pbVar4[8] != 0) {
      if ((uint)pbVar4[1] < (uint)*pbVar4) {
        iVar5 = (uint)pbVar4[1] * 8 + iVar3 * 0x6c;
        if (*(char *)(iVar5 + DAT_000076b8) == '\0') {
          iVar5 = DAT_000076b8 + iVar5;
          FUN_00008f88(3,DAT_000076c0,DAT_000076c4);
          iVar5 = (**(code **)(iVar5 + 4))();
          if (iVar5 == 0) {
            FUN_00008f88(1,uVar2,DAT_000076c8);
            pbVar4[8] = 0;
          }
          else {
LAB_000076ac:
            pbVar4[1] = pbVar4[1] + 1;
          }
        }
        else if (*(char *)(iVar5 + DAT_000076b8) == '\x01') {
          iVar5 = DAT_000076b8 + iVar5;
          if (*(int *)(pbVar4 + 4) == 0) {
            uVar2 = FUN_000077b4();
            *(undefined4 *)(pbVar4 + 4) = uVar2;
            FUN_00008f88(3,DAT_000076c0,DAT_000076d0,*(undefined4 *)(iVar5 + 4));
          }
          else {
            uVar6 = FUN_000077b4();
            if (((uint)((ulonglong)uVar6 >> 0x20) != (uint)((uint)uVar6 < *(uint *)(pbVar4 + 4))) ||
               (*(uint *)(iVar5 + 4) <= (uint)uVar6 - *(uint *)(pbVar4 + 4))) {
              FUN_00008f88(3,DAT_000076c0,DAT_000076d4);
              pbVar4[4] = 0;
              pbVar4[5] = 0;
              pbVar4[6] = 0;
              pbVar4[7] = 0;
              goto LAB_000076ac;
            }
          }
        }
        else {
          FUN_00008f88(1,DAT_000076c0,DAT_000076bc);
          pbVar4[8] = 0;
        }
        uVar1 = DAT_000076cc;
        uVar2 = DAT_000076c0;
        if (*pbVar4 <= pbVar4[1]) {
          pbVar4[8] = 0;
          FUN_00008f88(3,uVar2,uVar1);
        }
      }
      else {
        pbVar4[8] = 0;
      }
    }
    pbVar4 = pbVar4 + 0x6c;
    if (iVar3 == 1) {
      return;
    }
    iVar3 = 1;
  } while( true );
}


