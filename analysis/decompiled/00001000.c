/* UNREVIEWED Ghidra output: FUN_00001000 @ 00001000 */

uint FUN_00001000(uint param_1,uint param_2)

{
  uint uVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  uint uVar11;
  uint uVar12;
  
  uVar9 = param_1 & 0x7fffff;
  uVar6 = uVar9 * 8;
  uVar7 = param_2 & 0x7fffff;
  uVar11 = (param_1 & 0x7fffffff) >> 0x17;
  uVar10 = -((int)param_1 >> 0x1f);
  uVar8 = (param_2 & 0x7fffffff) >> 0x17;
  uVar4 = -((int)param_2 >> 0x1f);
  uVar3 = param_2 & 0x7fffff;
  uVar12 = uVar3 * 8;
  if (uVar8 == 0xff) {
    if (uVar3 == 0) {
      uVar5 = uVar4 ^ 1;
      if (uVar5 != uVar10) goto LAB_00001032;
    }
    else {
      uVar5 = uVar4;
      if (uVar10 != uVar4) {
        uVar1 = uVar11 - 0xff;
        goto LAB_000010ee;
      }
    }
    uVar1 = uVar11 - 0xff;
LAB_0000113a:
    if (uVar1 == 0) {
      uVar8 = uVar11 + 1;
      if ((uVar8 & 0xfe) == 0) {
        if (uVar11 != 0) {
          if (uVar9 != 0) {
LAB_000011e0:
            if (((uVar3 != 0) && ((param_1 & 0x400000) != 0)) && ((param_2 & 0x400000) == 0))
            goto LAB_000011f2;
            goto LAB_000011f6;
          }
          goto LAB_0000130e;
        }
        if (uVar9 == 0) {
          uVar1 = 0;
          uVar9 = uVar7;
          goto LAB_00001096;
        }
        uVar1 = 0;
        if (uVar3 == 0) goto LAB_00001096;
        uVar6 = uVar12 + uVar6;
        if ((int)(uVar6 * 0x20) < 0) {
          uVar11 = 1;
          uVar6 = uVar6 & DAT_00001348;
        }
LAB_000011c4:
        uVar1 = uVar11;
        if ((uVar6 & 7) != 0) goto LAB_00001078;
        goto LAB_000011ca;
      }
      if (uVar8 != 0xff) {
        uVar6 = uVar12 + uVar6 >> 1;
        uVar11 = uVar8;
        goto LAB_000011c4;
      }
    }
    else {
      uVar1 = uVar8 - uVar11;
      if (uVar11 != 0) {
        if (uVar8 != 0xff) {
          uVar6 = uVar6 | 0x4000000;
LAB_00001158:
          if ((int)uVar1 < 0x1c) {
            uVar6 = (uint)(uVar6 << (0x20 - uVar1 & 0xff) != 0) | uVar6 >> (uVar1 & 0xff);
          }
          else {
            uVar6 = 1;
          }
          uVar6 = uVar6 + uVar12;
          goto LAB_000010ca;
        }
LAB_0000130e:
        uVar9 = uVar7;
        goto LAB_000011f6;
      }
      if (uVar9 != 0) {
        if (uVar1 == 1) goto LAB_000012de;
        if (uVar1 != 0xff) {
          uVar1 = uVar1 - 1;
          goto LAB_00001158;
        }
        goto LAB_0000130e;
      }
LAB_000011cc:
      uVar9 = uVar7;
      if (uVar1 != 0xff) {
        uVar1 = uVar1 & 0xff;
        uVar9 = uVar7 & 0x7fffff;
        goto LAB_00001096;
      }
LAB_000011f6:
      if (uVar9 != 0) {
        uVar1 = 0xff;
        uVar9 = uVar9 & 0x7fffff | 0x400000;
        goto LAB_00001096;
      }
    }
  }
  else {
    uVar5 = uVar4 ^ 1;
    if (uVar10 != uVar5) {
LAB_00001032:
      uVar1 = uVar11 - uVar8;
      uVar5 = uVar4 ^ 1;
      if ((int)uVar1 < 1) {
LAB_000010ee:
        if (uVar1 == 0) {
          if ((uVar11 + 1 & 0xfe) == 0) {
            if (uVar11 != 0) {
              if (uVar9 == 0) {
                if (uVar3 == 0) {
                  uVar1 = 0xff;
                  uVar10 = 0;
                  uVar9 = 0x400000;
                  goto LAB_00001096;
                }
                goto LAB_000011f2;
              }
              goto LAB_000011e0;
            }
            if (uVar9 == 0) {
              if (uVar3 != 0) {
                uVar1 = 0;
                uVar10 = uVar5;
                uVar9 = uVar7;
                goto LAB_00001096;
              }
              goto LAB_00001260;
            }
            uVar1 = 0;
            if (uVar3 == 0) goto LAB_00001096;
            uVar6 = uVar6 + uVar3 * -8;
            if (-1 < (int)(uVar6 * 0x20)) {
              if (uVar6 == 0) {
                uVar10 = 0;
                uVar9 = 0;
                goto LAB_00001096;
              }
              goto LAB_000011c4;
            }
            uVar6 = uVar12 + uVar9 * -8;
            uVar10 = uVar5;
          }
          else {
            uVar6 = uVar6 + uVar3 * -8;
            if ((int)(uVar6 * 0x20) < 0) {
              uVar6 = uVar12 + uVar9 * -8;
              uVar10 = uVar5;
            }
            else if (uVar6 == 0) {
LAB_00001260:
              uVar10 = 0;
              uVar1 = 0;
              uVar9 = 0;
              goto LAB_00001096;
            }
LAB_0000105e:
            iVar2 = FUN_000023d0(uVar6);
            uVar3 = iVar2 - 5;
            uVar6 = uVar6 << (uVar3 & 0xff);
            if ((int)uVar3 < (int)uVar11) {
              uVar11 = uVar11 - uVar3;
              uVar6 = DAT_00001348 & uVar6;
            }
            else {
              uVar3 = (uVar3 - uVar11) + 1;
              uVar11 = 0;
              uVar6 = (uint)(uVar6 << (0x20 - uVar3 & 0xff) != 0) | uVar6 >> (uVar3 & 0xff);
            }
          }
          goto LAB_00001074;
        }
        uVar1 = uVar8 - uVar11;
        if (uVar11 == 0) {
          if (uVar9 == 0) {
            uVar10 = uVar5;
            goto LAB_000011cc;
          }
          uVar3 = uVar1 - 1;
          if (uVar1 == 1) {
            uVar11 = 1;
            uVar6 = uVar12 + uVar9 * -8;
            goto LAB_00001054;
          }
          if (uVar1 != 0xff) goto LAB_00001244;
        }
        else if (uVar8 != 0xff) {
          uVar6 = uVar6 | 0x4000000;
          uVar3 = uVar1;
LAB_00001244:
          if ((int)uVar3 < 0x1c) {
            uVar6 = (uint)(uVar6 << (0x20 - uVar3 & 0xff) != 0) | uVar6 >> (uVar3 & 0xff);
          }
          else {
            uVar6 = 1;
          }
          uVar6 = uVar12 - uVar6;
          uVar11 = uVar8;
          goto LAB_00001054;
        }
LAB_000011f2:
        uVar9 = uVar7;
        uVar10 = uVar5;
      }
      else {
        uVar5 = uVar10;
        if (uVar8 == 0) {
          if (uVar3 == 0) {
            uVar7 = uVar9;
            goto LAB_000011cc;
          }
          uVar7 = uVar1 - 1;
          if (uVar1 == 1) {
            uVar6 = uVar6 + uVar3 * -8;
            uVar11 = 1;
            goto LAB_00001054;
          }
          if (uVar1 != 0xff) goto LAB_00001048;
        }
        else if (uVar11 != 0xff) {
          uVar12 = uVar12 | 0x4000000;
          uVar7 = uVar1;
LAB_00001048:
          if ((int)uVar7 < 0x1c) {
            uVar3 = (uint)(uVar12 << (0x20 - uVar7 & 0xff) != 0) | uVar12 >> (uVar7 & 0xff);
          }
          else {
            uVar3 = 1;
          }
          uVar6 = uVar6 - uVar3;
LAB_00001054:
          uVar10 = uVar5;
          if ((int)(uVar6 << 5) < 0) {
            uVar6 = uVar6 & 0x3ffffff;
            goto LAB_0000105e;
          }
          goto LAB_000011c4;
        }
      }
      goto LAB_000011f6;
    }
    uVar1 = uVar11 - uVar8;
    if ((int)uVar1 < 1) goto LAB_0000113a;
    if (uVar8 == 0) {
      if (uVar3 == 0) {
        uVar7 = uVar9;
        goto LAB_000011cc;
      }
      uVar3 = uVar1 - 1;
      if (uVar1 != 1) {
        if (uVar1 != 0xff) goto LAB_000010be;
        goto LAB_000011f6;
      }
LAB_000012de:
      uVar6 = uVar12 + uVar6;
      uVar11 = 1;
      if (-1 < (int)(uVar6 * 0x20)) goto LAB_000011c4;
      uVar11 = 2;
    }
    else {
      if (uVar11 == 0xff) goto LAB_000011f6;
      uVar12 = uVar12 | 0x4000000;
      uVar3 = uVar1;
LAB_000010be:
      if ((int)uVar3 < 0x1c) {
        uVar3 = (uint)(uVar12 << (0x20 - uVar3 & 0xff) != 0) | uVar12 >> (uVar3 & 0xff);
      }
      else {
        uVar3 = 1;
      }
      uVar6 = uVar3 + uVar6;
      uVar8 = uVar11;
LAB_000010ca:
      uVar11 = uVar8;
      if (-1 < (int)(uVar6 << 5)) goto LAB_000011c4;
      uVar11 = uVar8 + 1;
      if (uVar11 == 0xff) goto LAB_000011ac;
    }
    uVar6 = uVar6 >> 1 & DAT_0000134c | uVar6 & 1;
LAB_00001074:
    if ((uVar6 & 7) != 0) {
LAB_00001078:
      if ((uVar6 & 0xf) != 4) {
        uVar6 = uVar6 + 4;
      }
    }
    uVar1 = uVar11;
    if (-1 < (int)(uVar6 << 5)) {
LAB_000011ca:
      uVar7 = uVar6 >> 3;
      goto LAB_000011cc;
    }
    if (uVar11 != 0xfe) {
      uVar1 = uVar11 + 1 & 0xff;
      uVar9 = (uVar6 & 0x3ffffff) >> 3;
      goto LAB_00001096;
    }
  }
LAB_000011ac:
  uVar1 = 0xff;
  uVar9 = 0;
LAB_00001096:
  return uVar1 << 0x17 | uVar9 | uVar10 << 0x1f;
}


