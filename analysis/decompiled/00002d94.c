/* UNREVIEWED Ghidra output: FUN_00002d94 @ 00002d94 */

void FUN_00002d94(undefined4 param_1,undefined4 param_2,int *param_3)

{
  int iVar1;
  char *local_3c;
  char local_38 [36];
  
  local_38[0] = '\0';
  local_38[1] = '\0';
  local_38[2] = '\0';
  local_38[3] = '\0';
  FUN_0000975a(local_38 + 4,0,0x1c);
  iVar1 = FUN_00002cb8(param_1,0x3c0,param_2,local_38);
  if (iVar1 != 0) {
    local_3c = (char *)0x0;
    iVar1 = FUN_00009a28(local_38,&local_3c,10);
    if (((local_3c == local_38) || (*local_3c != '\0')) || (iVar1 < 0)) {
      FUN_00008f88(1,DAT_00002df4,DAT_00002df0,param_2);
    }
    else {
      *param_3 = iVar1;
    }
  }
  return;
}


