/* UNREVIEWED Ghidra output: FUN_000006e8 @ 000006e8 */

uint FUN_000006e8(uint param_1,uint param_2)

{
  uint uVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  int iVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  
  uVar6 = param_1 & 0x7fffff;
  uVar4 = uVar6 * 8;
  iVar7 = -((int)param_1 >> 0x1f);
  uVar1 = param_2 & 0x7fffff;
  uVar8 = (param_1 & 0x7fffffff) >> 0x17;
  uVar10 = (param_2 & 0x7fffffff) >> 0x17;
  iVar3 = -((int)param_2 >> 0x1f);
  uVar2 = param_2 & 0x7fffff;
  uVar9 = uVar2 * 8;
  if (iVar7 == iVar3) {
    uVar5 = uVar8 - uVar10;
    if (0 < (int)uVar5) {
      if (uVar10 == 0) {
        if (uVar2 == 0) goto LAB_00000858;
        uVar2 = uVar5 - 1;
        if (uVar5 == 1) {
LAB_0000098c:
          uVar4 = uVar9 + uVar4;
          uVar8 = 1;
          iVar3 = iVar7;
          if (-1 < (int)(uVar4 * 0x20)) goto LAB_00000850;
          uVar8 = 2;
          goto LAB_000007ce;
        }
        if (uVar5 != 0xff) goto LAB_000007ba;
      }
      else if (uVar8 != 0xff) {
        uVar9 = uVar9 | 0x4000000;
        uVar2 = uVar5;
LAB_000007ba:
        if ((int)uVar2 < 0x1c) {
          uVar2 = (uint)(uVar9 << (0x20 - uVar2 & 0xff) != 0) | uVar9 >> (uVar2 & 0xff);
        }
        else {
          uVar2 = 1;
        }
        uVar4 = uVar2 + uVar4;
        uVar10 = uVar8;
LAB_000007c4:
        iVar3 = iVar7;
        uVar8 = uVar10;
        if (-1 < (int)(uVar4 << 5)) goto LAB_00000850;
        uVar8 = uVar10 + 1;
        if (uVar8 == 0xff) goto LAB_00000836;
LAB_000007ce:
        uVar4 = uVar4 >> 1 & DAT_00000a20 | uVar4 & 1;
        goto LAB_00000750;
      }
      goto LAB_0000087a;
    }
    if (uVar5 != 0) {
      uVar5 = uVar10 - uVar8;
      if (uVar8 == 0) {
        if (uVar6 == 0) goto LAB_000008e8;
        if (uVar5 == 1) goto LAB_0000098c;
        if (uVar5 != 0xff) {
          uVar5 = uVar5 - 1;
          goto LAB_000008aa;
        }
      }
      else if (uVar10 != 0xff) {
        uVar4 = uVar4 | 0x4000000;
LAB_000008aa:
        if ((int)uVar5 < 0x1c) {
          uVar4 = (uint)(uVar4 << (0x20 - uVar5 & 0xff) != 0) | uVar4 >> (uVar5 & 0xff);
        }
        else {
          uVar4 = 1;
        }
        uVar4 = uVar4 + uVar9;
        goto LAB_000007c4;
      }
LAB_00000878:
      uVar6 = uVar1;
      goto LAB_0000087a;
    }
    uVar10 = uVar8 + 1;
    if ((uVar10 & 0xfe) == 0) {
      if (uVar8 != 0) {
        if (uVar6 != 0) {
          if (((uVar2 != 0) && ((param_1 & 0x400000) != 0)) && ((param_2 & 0x400000) == 0)) {
            uVar6 = uVar1;
          }
          goto LAB_0000087a;
        }
        goto LAB_00000878;
      }
      if (uVar6 == 0) {
        uVar5 = 0;
        uVar6 = uVar1;
        goto LAB_00000772;
      }
      uVar5 = 0;
      if (uVar2 == 0) goto LAB_00000772;
      uVar4 = uVar9 + uVar4;
      iVar3 = iVar7;
      if ((int)(uVar4 * 0x20) < 0) {
        uVar8 = 1;
        uVar4 = uVar4 & DAT_00000a1c;
      }
LAB_00000850:
      uVar5 = uVar8;
      if ((uVar4 & 7) != 0) goto LAB_00000754;
      goto LAB_00000856;
    }
    if (uVar10 != 0xff) {
      uVar4 = uVar9 + uVar4 >> 1;
      iVar3 = iVar7;
      uVar8 = uVar10;
      goto LAB_00000850;
    }
  }
  else {
    uVar5 = uVar8 - uVar10;
    if ((int)uVar5 < 1) {
      if (uVar5 == 0) {
        if ((uVar8 + 1 & 0xfe) != 0) {
          uVar4 = uVar4 + uVar2 * -8;
          if ((int)(uVar4 * 0x20) < 0) {
            uVar4 = uVar9 + uVar6 * -8;
            iVar7 = iVar3;
          }
          else if (uVar4 == 0) goto LAB_00000918;
          goto LAB_0000073a;
        }
        if (uVar8 != 0) {
          if (uVar6 == 0) {
            if (uVar2 == 0) {
              uVar5 = 0xff;
              iVar7 = 0;
              uVar6 = 0x400000;
              goto LAB_00000772;
            }
          }
          else if (((uVar2 == 0) || ((param_1 & 0x400000) == 0)) || ((param_2 & 0x400000) != 0))
          goto LAB_0000087a;
          goto LAB_00000876;
        }
        if (uVar6 == 0) {
          if (uVar2 != 0) {
            uVar5 = 0;
            iVar7 = iVar3;
            uVar6 = uVar1;
            goto LAB_00000772;
          }
LAB_00000918:
          uVar5 = 0;
          iVar7 = 0;
          uVar6 = 0;
          goto LAB_00000772;
        }
        uVar5 = 0;
        if (uVar2 == 0) goto LAB_00000772;
        uVar4 = uVar4 + uVar2 * -8;
        if (-1 < (int)(uVar4 * 0x20)) {
          iVar3 = iVar7;
          if (uVar4 == 0) {
            iVar7 = 0;
            uVar6 = 0;
            goto LAB_00000772;
          }
          goto LAB_00000850;
        }
        uVar4 = uVar9 + uVar6 * -8;
        iVar7 = iVar3;
      }
      else {
        uVar5 = uVar10 - uVar8;
        if (uVar8 == 0) {
          if (uVar6 == 0) {
            iVar7 = iVar3;
LAB_000008e8:
            uVar6 = uVar1;
            goto LAB_00000858;
          }
          uVar2 = uVar5 - 1;
          if (uVar5 == 1) {
            uVar4 = uVar9 + uVar6 * -8;
            uVar8 = 1;
            goto LAB_00000730;
          }
          if (uVar5 == 0xff) goto LAB_00000876;
        }
        else {
          if (uVar10 == 0xff) {
LAB_00000876:
            iVar7 = iVar3;
            goto LAB_00000878;
          }
          uVar4 = uVar4 | 0x4000000;
          uVar2 = uVar5;
        }
        if ((int)uVar2 < 0x1c) {
          uVar4 = (uint)(uVar4 << (0x20 - uVar2 & 0xff) != 0) | uVar4 >> (uVar2 & 0xff);
        }
        else {
          uVar4 = 1;
        }
        uVar4 = uVar9 - uVar4;
        uVar8 = uVar10;
LAB_00000730:
        if (-1 < (int)(uVar4 << 5)) goto LAB_00000850;
        uVar4 = uVar4 & 0x3ffffff;
        iVar7 = iVar3;
LAB_0000073a:
        iVar3 = FUN_000023d0(uVar4);
        uVar2 = iVar3 - 5;
        uVar4 = uVar4 << (uVar2 & 0xff);
        if ((int)uVar2 < (int)uVar8) {
          uVar8 = uVar8 - uVar2;
          uVar4 = DAT_00000a1c & uVar4;
        }
        else {
          uVar2 = (uVar2 - uVar8) + 1;
          uVar8 = 0;
          uVar4 = (uint)(uVar4 << (0x20 - uVar2 & 0xff) != 0) | uVar4 >> (uVar2 & 0xff);
        }
      }
LAB_00000750:
      iVar3 = iVar7;
      if ((uVar4 & 7) != 0) {
LAB_00000754:
        if ((uVar4 & 0xf) != 4) {
          uVar4 = uVar4 + 4;
        }
      }
      uVar5 = uVar8;
      if ((int)(uVar4 << 5) < 0) {
        iVar7 = iVar3;
        if (uVar8 != 0xfe) {
          uVar5 = uVar8 + 1 & 0xff;
          uVar6 = (uVar4 & 0x3ffffff) >> 3;
          goto LAB_00000772;
        }
        goto LAB_00000836;
      }
LAB_00000856:
      uVar6 = uVar4 >> 3;
      iVar7 = iVar3;
LAB_00000858:
      if (uVar5 != 0xff) {
        uVar5 = uVar5 & 0xff;
        uVar6 = uVar6 & 0x7fffff;
        goto LAB_00000772;
      }
    }
    else if (uVar10 == 0) {
      if (uVar2 == 0) goto LAB_00000858;
      uVar10 = uVar5 - 1;
      if (uVar5 == 1) {
        uVar4 = uVar4 + uVar2 * -8;
        iVar3 = iVar7;
        uVar8 = 1;
        goto LAB_00000730;
      }
      if (uVar5 != 0xff) goto LAB_00000724;
    }
    else if (uVar8 != 0xff) {
      uVar9 = uVar9 | 0x4000000;
      uVar10 = uVar5;
LAB_00000724:
      if ((int)uVar10 < 0x1c) {
        uVar2 = (uint)(uVar9 << (0x20 - uVar10 & 0xff) != 0) | uVar9 >> (uVar10 & 0xff);
      }
      else {
        uVar2 = 1;
      }
      uVar4 = uVar4 - uVar2;
      iVar3 = iVar7;
      goto LAB_00000730;
    }
LAB_0000087a:
    if (uVar6 != 0) {
      uVar5 = 0xff;
      uVar6 = uVar6 & 0x7fffff | 0x400000;
      goto LAB_00000772;
    }
  }
LAB_00000836:
  uVar5 = 0xff;
  uVar6 = 0;
LAB_00000772:
  return uVar5 << 0x17 | uVar6 | iVar7 << 0x1f;
}


