/* UNREVIEWED Ghidra output: FUN_0000a8ec @ 0000a8ec */

void FUN_0000a8ec(undefined4 *param_1,int param_2)

{
  undefined4 *puVar1;
  int iVar2;
  int *piVar3;
  int *piVar4;
  int *piVar5;
  int iVar6;
  int *piVar7;
  
  if (param_2 == 0) {
    return;
  }
  piVar7 = (int *)(param_2 + -4);
  if (*piVar7 < 0) {
    piVar7 = (int *)((int)piVar7 + *piVar7);
  }
  FUN_0000aaac(param_1);
  puVar1 = DAT_0000a97c;
  piVar4 = (int *)*DAT_0000a97c;
  if (piVar4 != (int *)0x0) {
    if (piVar4 <= piVar7) {
      do {
        piVar5 = piVar4;
        piVar4 = (int *)piVar5[1];
        if (piVar4 == (int *)0x0) break;
      } while (piVar4 <= piVar7);
      piVar3 = (int *)((int)piVar5 + *piVar5);
      if (piVar3 == piVar7) {
        iVar2 = *piVar5 + *piVar7;
        *piVar5 = iVar2;
        if (piVar4 == (int *)((int)piVar5 + iVar2)) {
          iVar6 = piVar4[1];
          *piVar5 = *piVar4 + iVar2;
          piVar5[1] = iVar6;
        }
      }
      else if (piVar7 < piVar3) {
        *param_1 = 0xc;
      }
      else {
        if (piVar4 == (int *)((int)piVar7 + *piVar7)) {
          iVar2 = *piVar4;
          piVar4 = (int *)piVar4[1];
          *piVar7 = iVar2 + *piVar7;
        }
        piVar7[1] = (int)piVar4;
        piVar5[1] = (int)piVar7;
      }
      goto LAB_0000a910;
    }
    if (piVar4 == (int *)((int)piVar7 + *piVar7)) {
      iVar2 = *piVar4;
      piVar4 = (int *)piVar4[1];
      *piVar7 = iVar2 + *piVar7;
    }
  }
  piVar7[1] = (int)piVar4;
  *puVar1 = piVar7;
LAB_0000a910:
  FUN_0000aabc(param_1);
  return;
}


