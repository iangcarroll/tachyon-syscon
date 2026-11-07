/* UNREVIEWED Ghidra output: FUN_0000a8c6 @ 0000a8c6 */

void FUN_0000a8c6(uint param_1,uint param_2,int param_3)

{
  int iVar1;
  bool bVar2;
  
  if ((param_2 < param_1) && (param_1 < param_2 + param_3)) {
    while (bVar2 = param_3 != 0, param_3 = param_3 + -1, bVar2) {
      *(undefined1 *)(param_1 + param_3) = *(undefined1 *)(param_2 + param_3);
    }
  }
  else {
    for (iVar1 = 0; param_3 != iVar1; iVar1 = iVar1 + 1) {
      *(undefined1 *)(param_1 + iVar1) = *(undefined1 *)(param_2 + iVar1);
    }
  }
  return;
}


