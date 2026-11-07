/* UNREVIEWED Ghidra output: cmd_SET_RGB @ 00004364 */

bool cmd_SET_RGB(int param_1,code *param_2)

{
  undefined1 uVar1;
  int iVar2;
  undefined *puVar3;
  uint uVar4;
  uint uVar5;
  bool bVar6;
  int local_3c;
  undefined1 auStack_2c [4];
  undefined4 local_28;
  byte local_24;
  undefined1 local_20;
  undefined1 local_1f;
  undefined1 local_1e;
  undefined1 local_1d;
  byte local_1c;
  
  uVar5 = 0;
  local_28 = 0;
  local_24 = 0;
  local_3c = param_1;
  do {
    iVar2 = FUN_00009828(local_3c,0x3a);
    if ((iVar2 == 0) || (3 < iVar2 - local_3c)) goto LAB_0000438a;
    FUN_000098b4(auStack_2c,local_3c);
    auStack_2c[iVar2 - local_3c & 0xff] = 0;
    uVar4 = uVar5 & 0xff;
    puVar3 = DAT_0000440c;
    if ((uVar5 != 0) &&
       (((puVar3 = DAT_00004410, uVar4 != 1 && (puVar3 = PTR_s_B__0000b932_3_00004414, uVar4 != 2))
        && (puVar3 = PTR_s_Brightness__00004418, uVar4 != 3)))) {
      puVar3 = PTR_s_Pattern__0000441c;
    }
    (*param_2)(puVar3);
    (*param_2)(auStack_2c);
    uVar1 = FUN_000096aa(auStack_2c);
    auStack_2c[uVar5 + 4] = uVar1;
    local_3c = iVar2 + 1;
    uVar5 = uVar5 + 1;
  } while (uVar5 != 5);
  if (local_24 < 5) {
    local_20 = (undefined1)local_28;
    local_1f = local_28._1_1_;
    local_1e = local_28._2_1_;
    local_1c = local_24;
    local_1d = local_28._3_1_;
    iVar2 = FUN_00005c38();
    bVar6 = iVar2 == 0;
  }
  else {
LAB_0000438a:
    (*param_2)(DAT_00004408);
    bVar6 = false;
  }
  return bVar6;
}


