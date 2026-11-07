/* UNREVIEWED Ghidra output: FUN_00008fcc @ 00008fcc */

undefined8 FUN_00008fcc(undefined4 param_1,undefined4 param_2,int param_3,uint param_4,char param_5)

{
  int extraout_r2;
  char cVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  int iVar5;
  undefined8 uVar6;
  int iVar7;
  
  uVar6 = CONCAT44(param_2,param_1);
  iVar3 = 0;
  uVar2 = (uint)(byte)(param_5 + 0x37);
  iVar7 = param_3;
  do {
    iVar5 = (int)((ulonglong)uVar6 >> 0x20);
    uVar4 = (uint)uVar6;
    uVar6 = FUN_00000448(uVar4,iVar5,param_4,0,param_3,uVar2,iVar7);
    cVar1 = '0';
    if (9 < extraout_r2) {
      cVar1 = (char)uVar2;
    }
    *(char *)(param_3 + iVar3) = cVar1 + (char)extraout_r2;
    iVar3 = iVar3 + 1;
  } while ((iVar5 != 0) || (param_4 <= uVar4));
  return CONCAT44(param_3,iVar3);
}


