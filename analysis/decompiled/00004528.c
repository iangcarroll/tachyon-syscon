/* UNREVIEWED Ghidra output: FUN_00004528 @ 00004528 */

void FUN_00004528(int param_1,code *param_2)

{
  char cVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  undefined4 local_58;
  undefined1 auStack_54 [28];
  undefined1 auStack_38 [36];
  
  local_58 = 0;
  FUN_0000975a(auStack_54,0,0x1c);
  if (param_1 == 0) {
    iVar2 = FUN_000030e8();
  }
  else {
    iVar2 = FUN_000030ec();
  }
  iVar4 = 0;
  iVar5 = 0;
  do {
    if (iVar4 == iVar2) {
      (*param_2)(PTR_s_No_more_keys_found_000045d8);
      if (iVar5 != 0) {
        (*param_2)(PTR_s_WARNING___d_rejected_slot_s___re_000045dc,iVar5);
      }
      return;
    }
    FUN_0000976c(&local_58,0x20,DAT_000045cc,iVar4);
    if (param_1 == 0) {
      iVar3 = FUN_00003464(&local_58,auStack_38);
      if (iVar3 == 0) {
        cVar1 = FUN_00003098(iVar4);
        goto LAB_000045a8;
      }
LAB_00004572:
      (*param_2)(PTR_s__s____s_0000b942_7_000045d0,&local_58,auStack_38);
    }
    else {
      iVar3 = FUN_000032b0();
      if (iVar3 != 0) goto LAB_00004572;
      cVar1 = FUN_000030c0(iVar4);
LAB_000045a8:
      if (cVar1 != '\x01') {
        (*param_2)(PTR_s_slot__u_REJECTED_000045d4,iVar4);
        iVar5 = iVar5 + 1;
      }
    }
    FUN_000079d0();
    FUN_0000975a(auStack_38,0,0x20);
    iVar4 = iVar4 + 1;
  } while( true );
}


