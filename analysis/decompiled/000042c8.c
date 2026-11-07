/* UNREVIEWED Ghidra output: cmd_LEDSTATUS @ 000042c8 */

int cmd_LEDSTATUS(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined1 local_20;
  undefined1 local_1f;
  undefined1 local_1e;
  undefined1 local_1d;
  undefined1 local_1c;
  undefined1 local_1b;
  
  FUN_0000975a(&local_20,0,6);
  iVar1 = FUN_00005dc8(&local_20);
  if (iVar1 != 0) {
    uVar2 = FUN_00005df4(local_20);
    uVar3 = FUN_00005e0c(local_1b);
    (*param_2)(DAT_0000431c,uVar2,local_1f,local_1e,local_1d,local_1c,uVar3);
  }
  return iVar1;
}


