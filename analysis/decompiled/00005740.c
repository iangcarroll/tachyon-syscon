/* UNREVIEWED Ghidra output: FUN_00005740 @ 00005740 */

undefined8 FUN_00005740(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  byte *pbVar1;
  uint *puVar2;
  uint *puVar3;
  char *pcVar4;
  char *pcVar5;
  undefined4 uVar6;
  int iVar7;
  uint uVar8;
  uint *puVar9;
  char cVar10;
  
  pbVar1 = DAT_00005814;
  uVar8 = (uint)*DAT_00005814;
  iVar7 = FUN_000080f8(0);
  puVar3 = DAT_0000581c;
  puVar2 = DAT_00005818;
  if (iVar7 == 0) {
    *DAT_00005818 = *DAT_00005818 + 10;
    pcVar4 = DAT_00005820;
    *puVar3 = 0;
    pcVar5 = DAT_00005824;
    if ((*pcVar4 == '\0') && (*DAT_00005824 == '\0')) {
      if (DAT_00005828 < *puVar2) {
        FUN_00006a48();
        *pcVar5 = '\x01';
      }
    }
  }
  else {
    *DAT_00005830 = '\x01';
    *puVar3 = *puVar3 + 10;
    *puVar2 = 0;
  }
  iVar7 = 0;
  puVar9 = DAT_0000582c;
  while ((*puVar2 < *puVar9 || (puVar9[1] <= *puVar2))) {
    iVar7 = iVar7 + 1;
    puVar9 = puVar9 + 3;
    if (iVar7 == 3) {
LAB_0000579e:
      pcVar4 = DAT_00005830;
      cVar10 = *DAT_00005830;
      if (cVar10 != '\0') {
        if (*puVar3 < 0xc9) {
          cVar10 = '\0';
        }
        else {
          *pbVar1 = *pbVar1 + 1;
        }
      }
      if ((*pbVar1 != uVar8) && ((code *)*DAT_00005834 != (code *)0x0)) {
        (*(code *)*DAT_00005834)(*pbVar1,*DAT_00005838);
      }
      uVar6 = DAT_0000583c;
      if (cVar10 != '\0') {
        *pcVar4 = '\0';
        *pbVar1 = 0xff;
        FUN_00007880(uVar6);
        FUN_00008148(0,0,DAT_00005840,0,param_1,uVar8,param_3);
      }
      return CONCAT44(uVar8,param_1);
    }
  }
  *pbVar1 = (byte)DAT_0000582c[iVar7 * 3 + 2];
  goto LAB_0000579e;
}


