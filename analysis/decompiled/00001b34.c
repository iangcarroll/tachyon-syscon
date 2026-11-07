/* UNREVIEWED Ghidra output: FUN_00001b34 @ 00001b34 */

undefined8 FUN_00001b34(uint param_1,uint param_2,uint param_3,uint param_4)

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
  uint uVar13;
  uint uVar14;
  
  uVar4 = (param_2 & 0x7fffffff) >> 0x14;
  uVar5 = param_1 >> 0x1d;
  uVar6 = uVar5 | (param_2 & 0xfffff) << 3;
  uVar11 = -((int)param_2 >> 0x1f);
  uVar9 = param_1 * 8;
  uVar7 = param_3 >> 0x1d;
  uVar14 = param_3 * 8;
  uVar1 = (param_4 & 0x7fffffff) >> 0x14;
  uVar12 = -((int)param_4 >> 0x1f);
  uVar3 = (param_4 & 0xfffff) << 3 | uVar7;
  if (uVar1 == DAT_00001e8c) {
    if (uVar3 == 0 && uVar14 == 0) {
      uVar13 = uVar12 ^ 1;
      if (uVar11 != uVar13) goto LAB_00001b80;
    }
    else {
      uVar13 = uVar12;
      if (uVar11 != uVar12) {
        uVar8 = DAT_00001e94 + uVar4;
        goto LAB_00001ce8;
      }
    }
    uVar8 = DAT_00001e94 + uVar4;
LAB_00001d40:
    if (uVar8 == 0) {
      uVar8 = uVar4 + 1;
      if ((uVar8 & DAT_00002204) == 0) {
        if (uVar4 != 0) {
          if (uVar6 != 0 || uVar9 != 0) {
            if (uVar3 == 0 && uVar14 == 0) {
              uVar4 = param_1 & 0x1fffffff | uVar5 << 0x1d;
              uVar10 = param_2 & 0xfffff;
            }
            else {
              uVar4 = param_1 & 0x1fffffff | uVar5 << 0x1d;
              uVar10 = param_2 & 0xfffff;
              if ((param_2 & 0x80000) != 0) {
                if ((param_4 & 0x80000) == 0) {
                  uVar4 = param_3 & 0x1fffffff | uVar7 << 0x1d;
                  uVar10 = param_4 & 0xfffff;
                  uVar11 = uVar13;
                }
              }
            }
            goto LAB_00001e48;
          }
LAB_00002118:
          uVar4 = uVar7 << 0x1d | param_3 & 0x1fffffff;
          uVar10 = param_4 & 0xfffff;
          goto LAB_00001e48;
        }
        uVar8 = 0;
        if (uVar6 == 0 && uVar9 == 0) {
          uVar4 = uVar7 << 0x1d | param_3 & 0x1fffffff;
          uVar10 = param_4 & 0xfffff;
        }
        else {
          if (uVar3 != 0 || uVar14 != 0) {
            uVar5 = uVar9 + uVar14;
            uVar10 = uVar3 + uVar6 + (uint)(uVar5 < uVar9);
            if ((int)(uVar10 * 0x100) < 0) {
              uVar10 = uVar10 & DAT_0000220c;
              uVar4 = 1;
            }
            goto LAB_00001e10;
          }
          uVar4 = param_1 & 0x1fffffff | uVar5 << 0x1d;
          uVar10 = param_2 & 0xfffff;
        }
        goto LAB_00001e2a;
      }
      if (uVar8 == DAT_00002208) {
        uVar10 = 0;
        uVar4 = 0;
        goto LAB_00001c7a;
      }
      uVar4 = uVar3 + uVar6 + (uint)(uVar9 + uVar14 < uVar9);
      uVar10 = uVar4 >> 1;
      uVar5 = uVar4 * -0x80000000 | uVar9 + uVar14 >> 1;
      uVar4 = uVar8;
    }
    else {
      uVar8 = uVar1 - uVar4;
      if (uVar4 == 0) {
        if (uVar6 == 0 && uVar9 == 0) {
          uVar4 = uVar7 << 0x1d | param_3 & 0x1fffffff;
          uVar10 = param_4 & 0xfffff;
          goto LAB_00001e24;
        }
        if (uVar8 == 1) {
          uVar10 = uVar3 + uVar6 + (uint)(uVar9 + uVar14 < uVar14);
          goto LAB_0000206a;
        }
        if (uVar8 == DAT_00002208) {
          uVar4 = uVar7 << 0x1d | param_3 & 0x1fffffff;
          uVar10 = param_4 & 0xfffff;
          goto LAB_00001e48;
        }
        uVar8 = uVar8 - 1;
      }
      else {
        if (uVar1 == DAT_00001e8c) goto LAB_00002118;
        uVar6 = uVar6 | 0x800000;
      }
      if ((int)uVar8 < 0x39) {
        if ((int)uVar8 < 0x20) {
          uVar5 = uVar6 << (0x20 - uVar8 & 0xff) | uVar9 >> (uVar8 & 0xff) |
                  (uint)(uVar9 << (0x20 - uVar8 & 0xff) != 0);
          uVar3 = uVar3 + (uVar6 >> (uVar8 & 0xff));
        }
        else {
          if (uVar8 != 0x20) {
            uVar9 = uVar9 | uVar6 << (0x40 - uVar8 & 0xff);
          }
          uVar5 = (uint)(uVar9 != 0) | uVar6 >> (uVar8 - 0x20 & 0xff);
        }
      }
      else {
        uVar5 = (uint)(uVar6 != 0 || uVar9 != 0);
      }
      uVar5 = uVar5 + uVar14;
      uVar10 = (uVar5 < uVar14) + uVar3;
      uVar4 = uVar1;
LAB_00001f5a:
      if ((int)(uVar10 << 8) < 0) {
        uVar8 = uVar4 + 1;
        uVar4 = uVar8;
        if (uVar8 == DAT_00002208) {
          uVar10 = 0;
          uVar4 = 0;
          goto LAB_00001c7a;
        }
        goto LAB_00001f6e;
      }
    }
LAB_00001e10:
    uVar1 = uVar5;
    uVar8 = uVar4;
    if ((uVar5 & 7) != 0) {
LAB_00001c3c:
      uVar5 = uVar1;
      if ((uVar1 & 0xf) != 4) {
        uVar5 = uVar1 + 4;
        uVar10 = uVar10 + (uVar5 < uVar1);
      }
LAB_00001c50:
      uVar8 = uVar4;
      if ((int)(uVar10 << 8) < 0) {
        uVar8 = uVar4 + 1;
        if (uVar8 == DAT_00001e8c) {
          uVar10 = 0;
          uVar4 = 0;
        }
        else {
          uVar4 = (uVar10 & DAT_00001e90) << 0x1d | uVar5 >> 3;
          uVar8 = uVar8 & 0x7ff;
          uVar10 = (uVar10 & DAT_00001e90 & 0x7fffff) >> 3;
        }
        goto LAB_00001c7a;
      }
    }
    uVar4 = uVar10 << 0x1d | uVar5 >> 3;
    uVar10 = uVar10 >> 3;
LAB_00001e24:
    if (uVar8 != DAT_00001e8c) {
LAB_00001e2a:
      uVar10 = uVar10 & 0xfffff;
      uVar8 = uVar8 & 0x7ff;
      goto LAB_00001c7a;
    }
LAB_00001e48:
    if (uVar4 == 0 && uVar10 == 0) {
      uVar4 = 0;
      uVar10 = 0;
      uVar8 = DAT_00002254;
      goto LAB_00001c7a;
    }
  }
  else {
    uVar13 = uVar12 ^ 1;
    if (uVar11 == uVar13) {
      uVar8 = uVar4 - uVar1;
      if ((int)uVar8 < 1) goto LAB_00001d40;
      if (uVar1 != 0) {
        if (uVar4 == DAT_00001e8c) goto LAB_00001e3e;
        uVar3 = uVar3 | 0x800000;
LAB_00001cac:
        if ((int)uVar8 < 0x39) {
          if ((int)uVar8 < 0x20) {
            uVar5 = uVar3 << (0x20 - uVar8 & 0xff) | uVar14 >> (uVar8 & 0xff) |
                    (uint)(uVar14 << (0x20 - uVar8 & 0xff) != 0);
            uVar6 = uVar6 + (uVar3 >> (uVar8 & 0xff));
          }
          else {
            if (uVar8 != 0x20) {
              uVar14 = uVar14 | uVar3 << (0x40 - uVar8 & 0xff);
            }
            uVar5 = (uint)(uVar14 != 0) | uVar3 >> (uVar8 - 0x20 & 0xff);
          }
        }
        else {
          uVar5 = (uint)(uVar3 != 0 || uVar14 != 0);
        }
        uVar5 = uVar5 + uVar9;
        uVar10 = (uVar5 < uVar9) + uVar6;
        goto LAB_00001f5a;
      }
      if (uVar3 == 0 && uVar14 == 0) goto LAB_00001ea4;
      if (uVar8 != 1) {
        if (uVar8 != DAT_00001e8c) {
          uVar8 = uVar8 - 1;
          goto LAB_00001cac;
        }
        goto LAB_00001e3e;
      }
      uVar10 = uVar3 + uVar6 + (uint)(uVar9 + uVar14 < uVar9);
LAB_0000206a:
      uVar5 = uVar9 + uVar14;
      if (-1 < (int)(uVar10 << 8)) {
        uVar4 = 1;
        goto LAB_00001e10;
      }
      uVar4 = 2;
LAB_00001f6e:
      uVar5 = uVar5 & 1 | uVar5 >> 1 | (uVar10 & DAT_0000220c) << 0x1f;
      uVar10 = (uVar10 & DAT_0000220c) >> 1;
LAB_00001c38:
      uVar1 = uVar5;
      if ((uVar5 & 7) != 0) goto LAB_00001c3c;
      goto LAB_00001c50;
    }
LAB_00001b80:
    uVar12 = uVar12 ^ 1;
    uVar8 = uVar4 - uVar1;
    if (0 < (int)uVar8) {
      if (uVar1 != 0) {
        if (uVar4 == DAT_00001e8c) goto LAB_00001e3e;
        uVar3 = uVar3 | 0x800000;
LAB_00001b9e:
        if ((int)uVar8 < 0x39) {
          if ((int)uVar8 < 0x20) {
            uVar6 = uVar6 - (uVar3 >> (uVar8 & 0xff));
            uVar5 = (uint)(uVar14 << (0x20 - uVar8 & 0xff) != 0) |
                    uVar3 << (0x20 - uVar8 & 0xff) | uVar14 >> (uVar8 & 0xff);
          }
          else {
            if (uVar8 != 0x20) {
              uVar14 = uVar14 | uVar3 << (0x40 - uVar8 & 0xff);
            }
            uVar5 = (uint)(uVar14 != 0) | uVar3 >> (uVar8 - 0x20 & 0xff);
          }
        }
        else {
          uVar5 = (uint)(uVar14 != 0 || uVar3 != 0);
        }
        uVar5 = uVar9 - uVar5;
        uVar10 = uVar6 - (uVar9 < uVar5);
LAB_00001bd6:
        if ((int)(uVar10 << 8) < 0) {
          uVar10 = uVar10 & 0x7fffff;
          goto LAB_00001be6;
        }
        goto LAB_00001e10;
      }
      if (uVar3 != 0 || uVar14 != 0) {
        if (uVar8 == 1) {
          uVar5 = uVar9 + param_3 * -8;
          uVar10 = (uVar6 - uVar3) - (uint)(uVar9 < uVar5);
          uVar4 = 1;
          goto LAB_00001bd6;
        }
        if (uVar8 != DAT_00001e8c) {
          uVar8 = uVar8 - 1;
          goto LAB_00001b9e;
        }
LAB_00001e3e:
        uVar4 = param_1 & 0x1fffffff | uVar5 << 0x1d;
        uVar10 = param_2 & 0xfffff;
        goto LAB_00001e48;
      }
LAB_00001ea4:
      uVar4 = param_1 & 0x1fffffff | uVar5 << 0x1d;
      uVar10 = param_2 & 0xfffff;
      goto LAB_00001e24;
    }
LAB_00001ce8:
    if (uVar8 != 0) {
      uVar8 = uVar1 - uVar4;
      if (uVar4 == 0) {
        if (uVar6 == 0 && uVar9 == 0) {
          uVar4 = uVar7 << 0x1d | param_3 & 0x1fffffff;
          uVar10 = param_4 & 0xfffff;
          uVar11 = uVar12;
          goto LAB_00001e24;
        }
        uVar11 = uVar8 - 1;
        if (uVar8 == 1) {
          uVar5 = uVar14 + param_1 * -8;
          uVar10 = (uVar3 - uVar6) - (uint)(uVar14 < uVar5);
          uVar4 = 1;
          uVar11 = uVar12;
          goto LAB_00001bd6;
        }
        if (uVar8 != DAT_00001e8c) goto LAB_00001ef6;
      }
      else if (uVar1 != DAT_00002208) {
        uVar6 = uVar6 | 0x800000;
        uVar11 = uVar8;
LAB_00001ef6:
        if ((int)uVar11 < 0x39) {
          if ((int)uVar11 < 0x20) {
            uVar5 = (uint)(uVar9 << (0x20 - uVar11 & 0xff) != 0) |
                    uVar6 << (0x20 - uVar11 & 0xff) | uVar9 >> (uVar11 & 0xff);
            uVar3 = uVar3 - (uVar6 >> (uVar11 & 0xff));
          }
          else {
            if (uVar11 != 0x20) {
              uVar9 = uVar9 | uVar6 << (0x40 - uVar11 & 0xff);
            }
            uVar5 = uVar6 >> (uVar11 - 0x20 & 0xff) | (uint)(uVar9 != 0);
          }
        }
        else {
          uVar5 = (uint)(uVar6 != 0 || uVar9 != 0);
        }
        uVar5 = uVar14 - uVar5;
        uVar10 = uVar3 - (uVar14 < uVar5);
        uVar11 = uVar12;
        uVar4 = uVar1;
        goto LAB_00001bd6;
      }
LAB_0000208c:
      uVar4 = uVar7 << 0x1d | param_3 & 0x1fffffff;
      uVar10 = param_4 & 0xfffff;
      uVar11 = uVar12;
      goto LAB_00001e48;
    }
    uVar8 = 0;
    if ((uVar4 + 1 & DAT_00001e98) != 0) {
      uVar5 = uVar9 + param_3 * -8;
      uVar10 = (uVar6 - uVar3) - (uint)(uVar9 < uVar5);
      if ((int)(uVar10 * 0x100) < 0) {
        uVar5 = uVar14 + param_1 * -8;
        uVar10 = (uVar3 - uVar6) - (uint)(uVar14 < uVar5);
        uVar11 = uVar12;
      }
      else if (uVar10 == 0 && uVar5 == 0) goto LAB_00001f40;
LAB_00001be6:
      if (uVar10 == 0) {
        iVar2 = FUN_000023d0(uVar5);
        uVar1 = iVar2 + 0x18;
        if ((int)uVar1 < 0x20) goto LAB_00001bf8;
        uVar3 = uVar5 << (iVar2 - 8U & 0xff);
        uVar5 = 0;
      }
      else {
        iVar2 = FUN_000023d0(uVar10);
        uVar1 = iVar2 - 8;
LAB_00001bf8:
        uVar3 = uVar5 >> (0x20 - uVar1 & 0xff);
        uVar5 = uVar5 << (uVar1 & 0xff);
        uVar3 = uVar10 << (uVar1 & 0xff) | uVar3;
      }
      if ((int)uVar1 < (int)uVar4) {
        uVar4 = uVar4 - uVar1;
        uVar10 = uVar3 & DAT_00001e90;
      }
      else {
        uVar6 = (uVar1 - uVar4) + 1;
        if (0x1f < (int)uVar6) {
          if (uVar6 != 0x20) {
            uVar5 = uVar5 | uVar3 << (0x40 - uVar6 & 0xff);
          }
          uVar10 = 0;
          uVar5 = (uint)(uVar5 != 0) | uVar3 >> ((uVar1 - uVar4) - 0x1f & 0xff);
          uVar4 = 0;
          goto LAB_00001e10;
        }
        uVar10 = uVar3 >> (uVar6 & 0xff);
        uVar4 = 0;
        uVar5 = (uint)(uVar5 << (0x20 - uVar6 & 0xff) != 0) |
                uVar3 << (0x20 - uVar6 & 0xff) | uVar5 >> (uVar6 & 0xff);
      }
      goto LAB_00001c38;
    }
    if (uVar4 == 0) {
      if (uVar6 == 0 && uVar9 == 0) {
        if (uVar3 == 0 && uVar14 == 0) {
LAB_00001f40:
          uVar4 = 0;
          uVar10 = 0;
          uVar11 = 0;
        }
        else {
          uVar4 = uVar7 << 0x1d | param_3 & 0x1fffffff;
          uVar10 = param_4 & 0xfffff;
          uVar11 = uVar12;
        }
      }
      else {
        if (!(uVar3 == 0 && uVar14 == 0)) {
          uVar5 = uVar9 + param_3 * -8;
          uVar10 = (uVar6 - uVar3) - (uint)(uVar9 < uVar5);
          if (-1 < (int)(uVar10 * 0x100)) {
            if (uVar10 == 0 && uVar5 == 0) goto LAB_00001f40;
            goto LAB_00001e10;
          }
          uVar5 = uVar14 + param_1 * -8;
          uVar10 = (uVar3 - uVar6) - (uint)(uVar14 < uVar5);
          uVar11 = uVar12;
          goto LAB_00001c38;
        }
        uVar4 = param_1 & 0x1fffffff | uVar5 << 0x1d;
        uVar10 = param_2 & 0xfffff;
      }
      goto LAB_00001e2a;
    }
    if (uVar6 != 0 || uVar9 != 0) {
      if (uVar3 == 0 && uVar14 == 0) goto LAB_00001e3e;
      uVar4 = param_1 & 0x1fffffff | uVar5 << 0x1d;
      uVar10 = param_2 & 0xfffff;
      if ((param_2 & 0x80000) != 0) {
        if ((param_4 & 0x80000) == 0) {
          uVar4 = param_3 & 0x1fffffff | uVar7 << 0x1d;
          uVar10 = param_4 & 0xfffff;
          uVar11 = uVar12;
        }
      }
      goto LAB_00001e48;
    }
    if (uVar3 != 0 || uVar14 != 0) goto LAB_0000208c;
    uVar11 = 0;
    uVar10 = 0x80000;
    uVar4 = 0;
  }
  uVar10 = uVar10 & 0xfffff | 0x80000;
  uVar8 = DAT_00001e8c;
LAB_00001c7a:
  return CONCAT44(uVar8 << 0x14 | uVar10 | uVar11 << 0x1f,uVar4);
}


