/* UNREVIEWED Ghidra output: FUN_00009b24 @ 00009b24 */

byte * FUN_00009b24(undefined4 *param_1,int *param_2,byte *param_3,int *param_4)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  bool bVar4;
  byte *pbVar5;
  undefined4 *local_88;
  int *local_7c;
  uint local_78;
  int local_74;
  undefined4 local_70;
  int local_6c;
  byte *local_64;
  byte local_60;
  undefined1 local_5f;
  undefined1 local_5e;
  undefined1 local_35;
  undefined4 local_20;
  
  if (((int)((uint)*(ushort *)(param_2 + 3) << 0x18) < 0) && (param_2[4] == 0)) {
    iVar1 = FUN_0000a980(param_1,0x40);
    *param_2 = iVar1;
    param_2[4] = iVar1;
    if (iVar1 == 0) {
      *param_1 = 0xc;
      return (byte *)0xffffffff;
    }
    param_2[5] = 0x40;
  }
  local_64 = (byte *)0x0;
  local_5f = 0x20;
  local_5e = 0x30;
  local_7c = param_4;
  do {
    for (pbVar5 = param_3; (*pbVar5 != 0 && (*pbVar5 != 0x25)); pbVar5 = pbVar5 + 1) {
    }
    if (pbVar5 != param_3) {
      iVar1 = FUN_00009a60(param_1,param_2,param_3);
      if (iVar1 == -1) {
LAB_00009cec:
        if ((int)((uint)*(ushort *)(param_2 + 3) << 0x19) < 0) {
          local_64 = (byte *)0xffffffff;
        }
        return local_64;
      }
      local_64 = pbVar5 + ((int)local_64 - (int)param_3);
    }
    if (*pbVar5 == 0) goto LAB_00009cec;
    local_74 = -1;
    local_78 = 0;
    local_6c = 0;
    local_70 = 0;
    local_35 = 0;
    local_20 = 0;
    pbVar5 = pbVar5 + 1;
    while( true ) {
      iVar2 = FUN_0000a8b0(DAT_00009d10,*pbVar5,5);
      iVar1 = DAT_00009d14;
      param_3 = pbVar5 + 1;
      if (iVar2 == 0) break;
      local_78 = 1 << (iVar2 - DAT_00009d10 & 0xffU) | local_78;
      pbVar5 = param_3;
    }
    if ((int)(local_78 << 0x1b) < 0) {
      local_35 = 0x20;
    }
    if ((int)(local_78 << 0x1c) < 0) {
      local_35 = 0x2b;
    }
    if (*pbVar5 == 0x2a) {
      piVar3 = local_7c + 1;
      iVar2 = *local_7c;
      local_7c = piVar3;
      if (-1 < iVar2) goto LAB_00009c28;
      local_6c = -iVar2;
      local_78 = local_78 | 2;
    }
    else {
      bVar4 = false;
      iVar2 = local_6c;
      param_3 = pbVar5;
      while( true ) {
        if (9 < *param_3 - 0x30) break;
        bVar4 = true;
        iVar2 = iVar2 * 10 + (*param_3 - 0x30);
        param_3 = param_3 + 1;
      }
      if (bVar4) {
LAB_00009c28:
        local_6c = iVar2;
      }
    }
    if (*param_3 == 0x2e) {
      if (param_3[1] == 0x2a) {
        param_3 = param_3 + 2;
        local_74 = *local_7c;
        if (local_74 < 0) {
          local_74 = -1;
        }
        local_7c = local_7c + 1;
      }
      else {
        bVar4 = false;
        iVar2 = 0;
        local_74 = 0;
        while( true ) {
          param_3 = param_3 + 1;
          if (9 < *param_3 - 0x30) break;
          bVar4 = true;
          iVar2 = iVar2 * 10 + (*param_3 - 0x30);
        }
        if (bVar4) {
          local_74 = iVar2;
        }
      }
    }
    iVar2 = FUN_0000a8b0(DAT_00009d14,*param_3,3);
    if (iVar2 != 0) {
      param_3 = param_3 + 1;
      local_78 = 0x40 << (iVar2 - iVar1 & 0xffU) | local_78;
    }
    local_60 = *param_3;
    param_3 = param_3 + 1;
    iVar1 = FUN_0000a8b0(DAT_00009d18,local_60,6);
    if (iVar1 == 0) {
      local_88 = (undefined4 *)FUN_0000a1b4(param_1,&local_78,param_2,DAT_00009d20,&local_7c);
LAB_00009ce4:
      if (local_88 == (undefined4 *)0xffffffff) goto LAB_00009cec;
    }
    else {
      if (DAT_00009d1c != 0) {
        local_88 = param_1;
        goto LAB_00009ce4;
      }
      local_7c = (int *)(((int)local_7c + 7U & 0xfffffff8) + 8);
    }
    local_64 = local_64 + (int)local_88;
  } while( true );
}


