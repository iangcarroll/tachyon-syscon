/* UNREVIEWED Ghidra output: FUN_000092ac @ 000092ac */

undefined4 FUN_000092ac(int param_1,int param_2)

{
  undefined4 uVar1;
  code *pcVar2;
  int local_24;
  int local_20;
  undefined4 local_1c;
  
  local_1c = 0;
  pcVar2 = DAT_000092ec;
  if (param_1 == 0) {
    pcVar2 = DAT_000092f0;
  }
  local_24 = param_1;
  local_20 = param_2;
  uVar1 = FUN_00009038(pcVar2,&local_24);
  (*pcVar2)(0,&local_24);
  if ((param_1 != 0) && (param_2 != 0)) {
    *(undefined1 *)(param_1 + param_2 + -1) = 0;
  }
  return uVar1;
}


