/* UNREVIEWED Ghidra output: FUN_000014bc @ 000014bc */

undefined8 FUN_000014bc(uint param_1,uint param_2,uint param_3,uint param_4)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  int iVar8;
  uint uVar9;
  uint uVar10;
  uint uVar11;
  
  uVar3 = param_1 >> 0x1d;
  uVar1 = (param_2 & 0xfffff) << 3 | uVar3;
  uVar4 = (param_4 & 0x7fffffff) >> 0x14;
  uVar7 = param_1 * 8;
  iVar5 = -((int)param_4 >> 0x1f);
  uVar10 = param_3 >> 0x1d;
  uVar11 = uVar10 | (param_4 & 0xfffff) << 3;
  uVar9 = (param_2 & 0x7fffffff) >> 0x14;
  iVar8 = -((int)param_2 >> 0x1f);
  uVar2 = param_3 * 8;
  if (iVar8 == iVar5) {
    uVar6 = uVar9 - uVar4;
    if ((int)uVar6 < 1) {
      if (uVar6 == 0) {
        uVar4 = uVar9 + 1;
        if ((uVar4 & DAT_0000182c) != 0) {
          if (uVar4 != DAT_00001b2c) {
            uVar3 = uVar1 + uVar11 + (uint)(uVar7 + uVar2 < uVar7);
            uVar10 = uVar3 * -0x80000000 | uVar7 + uVar2 >> 1;
            uVar3 = uVar3 >> 1;
            uVar9 = uVar4;
            goto LAB_00001706;
          }
LAB_0000174a:
          uVar3 = 0;
          uVar1 = 0;
          goto LAB_000015ea;
        }
        if (uVar9 == 0) {
          if (uVar1 == 0 && uVar7 == 0) {
            uVar1 = uVar10 << 0x1d | param_3 & 0x1fffffff;
            uVar3 = param_4 & 0xfffff;
          }
          else {
            if (uVar11 != 0 || uVar2 != 0) {
              uVar10 = uVar7 + uVar2;
              uVar3 = uVar1 + uVar11 + (uint)(uVar10 < uVar7);
              if ((int)(uVar3 * 0x100) < 0) {
                uVar9 = 1;
                uVar3 = uVar3 & DAT_00001b30;
              }
              goto LAB_00001706;
            }
            uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
            uVar3 = param_2 & 0xfffff;
          }
          goto LAB_0000171c;
        }
        if (uVar1 != 0 || uVar7 != 0) {
          if (uVar11 != 0 || uVar2 != 0) {
            uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
            uVar3 = param_2 & 0xfffff;
            if (((param_2 & 0x80000) != 0) && ((param_4 & 0x80000) == 0)) {
              uVar1 = param_3 & 0x1fffffff | uVar10 << 0x1d;
              uVar3 = param_4 & 0xfffff;
            }
            goto LAB_00001758;
          }
          goto LAB_000019a8;
        }
      }
      else {
        uVar6 = uVar4 - uVar9;
        if (uVar9 == 0) {
          if (uVar1 == 0 && uVar7 == 0) {
            uVar1 = uVar10 << 0x1d | param_3 & 0x1fffffff;
            uVar3 = param_4 & 0xfffff;
            goto LAB_00001716;
          }
          if (uVar6 == 1) {
            uVar3 = uVar1 + uVar11 + (uint)(uVar7 + uVar2 < uVar2);
            goto LAB_000018aa;
          }
          if (uVar6 != DAT_00001b2c) {
            uVar6 = uVar6 - 1;
            goto LAB_000017b2;
          }
        }
        else if (uVar4 != DAT_00001824) {
          uVar1 = uVar1 | 0x800000;
LAB_000017b2:
          if ((int)uVar6 < 0x39) {
            if ((int)uVar6 < 0x20) {
              uVar10 = uVar1 << (0x20 - uVar6 & 0xff) | uVar7 >> (uVar6 & 0xff) |
                       (uint)(uVar7 << (0x20 - uVar6 & 0xff) != 0);
              uVar11 = uVar11 + (uVar1 >> (uVar6 & 0xff));
            }
            else {
              if (uVar6 != 0x20) {
                uVar7 = uVar7 | uVar1 << (0x40 - uVar6 & 0xff);
              }
              uVar10 = uVar1 >> (uVar6 - 0x20 & 0xff) | (uint)(uVar7 != 0);
            }
          }
          else {
            uVar10 = (uint)(uVar7 != 0 || uVar1 != 0);
          }
          uVar10 = uVar10 + uVar2;
          uVar3 = (uVar10 < uVar2) + uVar11;
          uVar9 = uVar4;
          goto LAB_0000173a;
        }
      }
      uVar1 = uVar10 << 0x1d | param_3 & 0x1fffffff;
      uVar3 = param_4 & 0xfffff;
    }
    else {
      if (uVar4 == 0) {
        if (uVar11 == 0 && uVar2 == 0) {
          uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
          uVar3 = param_2 & 0xfffff;
          goto LAB_00001716;
        }
        uVar4 = uVar6 - 1;
        if (uVar6 == 1) {
          uVar3 = uVar1 + uVar11 + (uint)(uVar7 + uVar2 < uVar7);
LAB_000018aa:
          uVar10 = uVar7 + uVar2;
          uVar9 = 1;
          if (-1 < (int)(uVar3 << 8)) goto LAB_00001706;
          uVar4 = 2;
          goto LAB_000018b4;
        }
        if (uVar6 != DAT_00001824) goto LAB_00001652;
      }
      else if (uVar9 != DAT_00001824) {
        uVar11 = uVar11 | 0x800000;
        uVar4 = uVar6;
LAB_00001652:
        if ((int)uVar4 < 0x39) {
          if ((int)uVar4 < 0x20) {
            uVar10 = uVar11 << (0x20 - uVar4 & 0xff) | uVar2 >> (uVar4 & 0xff) |
                     (uint)(uVar2 << (0x20 - uVar4 & 0xff) != 0);
            uVar1 = uVar1 + (uVar11 >> (uVar4 & 0xff));
          }
          else {
            if (uVar4 != 0x20) {
              uVar2 = uVar2 | uVar11 << (0x40 - uVar4 & 0xff);
            }
            uVar10 = (uint)(uVar2 != 0) | uVar11 >> (uVar4 - 0x20 & 0xff);
          }
        }
        else {
          uVar10 = (uint)(uVar11 != 0 || uVar2 != 0);
        }
        uVar10 = uVar10 + uVar7;
        uVar3 = (uVar10 < uVar7) + uVar1;
LAB_0000173a:
        if (-1 < (int)(uVar3 << 8)) goto LAB_00001706;
        uVar4 = uVar9 + 1;
        if (uVar4 == DAT_00001824) goto LAB_0000174a;
LAB_000018b4:
        uVar10 = uVar10 & 1 | uVar10 >> 1 | (uVar3 & DAT_00001b30) << 0x1f;
        uVar3 = (uVar3 & DAT_00001b30) >> 1;
        iVar5 = iVar8;
        uVar9 = uVar4;
        goto LAB_000015b0;
      }
LAB_000019a8:
      uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
      uVar3 = param_2 & 0xfffff;
    }
LAB_00001758:
    if (uVar1 == 0 && uVar3 == 0) {
      uVar1 = 0;
      uVar3 = 0;
      uVar4 = DAT_00001b2c;
      goto LAB_000015ea;
    }
  }
  else {
    uVar6 = uVar9 - uVar4;
    if (0 < (int)uVar6) {
      if (uVar4 != 0) {
        if (uVar9 != DAT_00001824) {
          uVar11 = uVar11 | 0x800000;
          goto LAB_00001520;
        }
LAB_00001750:
        uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
        uVar3 = param_2 & 0xfffff;
        goto LAB_00001758;
      }
      if (uVar11 != 0 || uVar2 != 0) {
        if (uVar6 == 1) {
          uVar10 = uVar7 + param_3 * -8;
          uVar9 = 1;
          uVar3 = (uVar1 - uVar11) - (uint)(uVar7 < uVar10);
          goto LAB_0000155e;
        }
        if (uVar6 == DAT_00001824) goto LAB_00001750;
        uVar6 = uVar6 - 1;
LAB_00001520:
        if ((int)uVar6 < 0x39) {
          if ((int)uVar6 < 0x20) {
            uVar10 = (uint)(uVar2 << (0x20 - uVar6 & 0xff) != 0) |
                     uVar11 << (0x20 - uVar6 & 0xff) | uVar2 >> (uVar6 & 0xff);
            uVar1 = uVar1 - (uVar11 >> (uVar6 & 0xff));
          }
          else {
            if (uVar6 != 0x20) {
              uVar2 = uVar2 | uVar11 << (0x40 - uVar6 & 0xff);
            }
            uVar10 = (uint)(uVar2 != 0) | uVar11 >> (uVar6 - 0x20 & 0xff);
          }
        }
        else {
          uVar10 = (uint)(uVar11 != 0 || uVar2 != 0);
        }
        uVar10 = uVar7 - uVar10;
        uVar3 = uVar1 - (uVar7 < uVar10);
LAB_0000155e:
        if ((int)(uVar3 << 8) < 0) {
          uVar3 = uVar3 & 0x7fffff;
          iVar5 = iVar8;
          goto LAB_00001568;
        }
LAB_00001706:
        uVar1 = uVar10;
        if ((uVar10 & 7) != 0) goto LAB_000015b4;
        goto LAB_0000170c;
      }
      uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
      uVar3 = param_2 & 0xfffff;
LAB_00001716:
      if (uVar6 != DAT_00001824) {
LAB_0000171c:
        uVar3 = uVar3 & 0xfffff;
        uVar4 = uVar6 & 0x7ff;
        goto LAB_000015ea;
      }
      goto LAB_00001758;
    }
    if (uVar6 != 0) {
      uVar6 = uVar4 - uVar9;
      if (uVar9 == 0) {
        if (uVar1 == 0 && uVar7 == 0) {
          uVar1 = uVar10 << 0x1d | param_3 & 0x1fffffff;
          uVar3 = param_4 & 0xfffff;
          iVar8 = iVar5;
          goto LAB_00001716;
        }
        uVar9 = uVar6 - 1;
        if (uVar6 == 1) {
          uVar10 = uVar2 + param_1 * -8;
          uVar9 = 1;
          uVar3 = (uVar11 - uVar1) - (uint)(uVar2 < uVar10);
          iVar8 = iVar5;
          goto LAB_0000155e;
        }
        if (uVar6 != DAT_00001824) goto LAB_00001866;
      }
      else if (uVar4 != DAT_00001b2c) {
        uVar1 = uVar1 | 0x800000;
        uVar9 = uVar6;
LAB_00001866:
        if ((int)uVar9 < 0x39) {
          if ((int)uVar9 < 0x20) {
            uVar11 = uVar11 - (uVar1 >> (uVar9 & 0xff));
            uVar10 = (uint)(uVar7 << (0x20 - uVar9 & 0xff) != 0) |
                     uVar1 << (0x20 - uVar9 & 0xff) | uVar7 >> (uVar9 & 0xff);
          }
          else {
            if (uVar9 != 0x20) {
              uVar7 = uVar7 | uVar1 << (0x40 - uVar9 & 0xff);
            }
            uVar10 = (uint)(uVar7 != 0) | uVar1 >> (uVar9 - 0x20 & 0xff);
          }
        }
        else {
          uVar10 = (uint)(uVar7 != 0 || uVar1 != 0);
        }
        uVar10 = uVar2 - uVar10;
        uVar3 = uVar11 - (uVar2 < uVar10);
        iVar8 = iVar5;
        uVar9 = uVar4;
        goto LAB_0000155e;
      }
LAB_000019bc:
      uVar1 = uVar10 << 0x1d | param_3 & 0x1fffffff;
      uVar3 = param_4 & 0xfffff;
      iVar8 = iVar5;
      goto LAB_00001758;
    }
    if ((uVar9 + 1 & DAT_0000182c) != 0) {
      uVar10 = uVar7 + param_3 * -8;
      uVar3 = (uVar1 - uVar11) - (uint)(uVar7 < uVar10);
      if ((int)(uVar3 * 0x100) < 0) {
        uVar10 = uVar2 + param_1 * -8;
        uVar3 = (uVar11 - uVar1) - (uint)(uVar2 < uVar10);
      }
      else {
        iVar5 = iVar8;
        if (uVar10 == 0 && uVar3 == 0) goto LAB_00001852;
      }
LAB_00001568:
      if (uVar3 == 0) {
        iVar8 = FUN_000023d0(uVar10);
        uVar1 = iVar8 + 0x18;
        if ((int)uVar1 < 0x20) goto LAB_00001578;
        uVar2 = uVar10 << (iVar8 - 8U & 0xff);
        uVar10 = 0;
      }
      else {
        iVar8 = FUN_000023d0(uVar3);
        uVar1 = iVar8 - 8;
LAB_00001578:
        uVar2 = uVar10 >> (0x20 - uVar1 & 0xff);
        uVar10 = uVar10 << (uVar1 & 0xff);
        uVar2 = uVar3 << (uVar1 & 0xff) | uVar2;
      }
      if ((int)uVar1 < (int)uVar9) {
        uVar9 = uVar9 - uVar1;
        uVar3 = uVar2 & DAT_00001828;
      }
      else {
        iVar8 = uVar1 - uVar9;
        uVar1 = iVar8 + 1;
        if (0x1f < (int)uVar1) {
          if (uVar1 != 0x20) {
            uVar10 = uVar10 | uVar2 << (0x40 - uVar1 & 0xff);
          }
          uVar3 = 0;
          uVar9 = 0;
          uVar10 = (uint)(uVar10 != 0) | uVar2 >> (iVar8 - 0x1fU & 0xff);
          iVar8 = iVar5;
          goto LAB_00001706;
        }
        uVar3 = uVar2 >> (uVar1 & 0xff);
        uVar9 = 0;
        uVar10 = (uint)(uVar10 << (0x20 - uVar1 & 0xff) != 0) |
                 uVar2 << (0x20 - uVar1 & 0xff) | uVar10 >> (uVar1 & 0xff);
      }
LAB_000015b0:
      uVar1 = uVar10;
      iVar8 = iVar5;
      if ((uVar10 & 7) != 0) {
LAB_000015b4:
        uVar10 = uVar1;
        if ((uVar1 & 0xf) != 4) {
          uVar10 = uVar1 + 4;
          uVar3 = uVar3 + (uVar10 < uVar1);
        }
      }
      if ((int)(uVar3 << 8) < 0) {
        uVar4 = uVar9 + 1;
        if (uVar4 != DAT_00001824) {
          uVar1 = (uVar3 & DAT_00001828) << 0x1d | uVar10 >> 3;
          uVar3 = (uVar3 & DAT_00001828 & 0x7fffff) >> 3;
          uVar4 = uVar4 & 0x7ff;
          goto LAB_000015ea;
        }
        goto LAB_0000174a;
      }
LAB_0000170c:
      uVar1 = uVar3 << 0x1d | uVar10 >> 3;
      uVar3 = uVar3 >> 3;
      uVar6 = uVar9;
      goto LAB_00001716;
    }
    if (uVar9 == 0) {
      if (uVar1 == 0 && uVar7 == 0) {
        if (uVar11 == 0 && uVar2 == 0) goto LAB_00001852;
        uVar1 = uVar10 << 0x1d | param_3 & 0x1fffffff;
        uVar3 = param_4 & 0xfffff;
        iVar8 = iVar5;
      }
      else if (uVar11 == 0 && uVar2 == 0) {
        uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
        uVar3 = param_2 & 0xfffff;
      }
      else {
        uVar10 = uVar7 + param_3 * -8;
        uVar3 = (uVar1 - uVar11) - (uint)(uVar7 < uVar10);
        if ((int)(uVar3 * 0x100) < 0) {
          uVar10 = uVar2 + param_1 * -8;
          uVar3 = (uVar11 - uVar1) - (uint)(uVar2 < uVar10);
          goto LAB_000015b0;
        }
        if (uVar10 != 0 || uVar3 != 0) goto LAB_00001706;
LAB_00001852:
        uVar1 = 0;
        uVar3 = 0;
        iVar8 = 0;
      }
      goto LAB_0000171c;
    }
    if (uVar1 != 0 || uVar7 != 0) {
      if (uVar11 == 0 && uVar2 == 0) {
        uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
        uVar3 = param_2 & 0xfffff;
      }
      else {
        uVar1 = param_1 & 0x1fffffff | uVar3 << 0x1d;
        uVar3 = param_2 & 0xfffff;
        if ((param_2 & 0x80000) != 0) {
          if ((param_4 & 0x80000) == 0) {
            uVar1 = param_3 & 0x1fffffff | uVar10 << 0x1d;
            uVar3 = param_4 & 0xfffff;
            iVar8 = iVar5;
          }
        }
      }
      goto LAB_00001758;
    }
    if (uVar11 != 0 || uVar2 != 0) goto LAB_000019bc;
    iVar8 = 0;
    uVar3 = 0x80000;
    uVar1 = 0;
  }
  uVar3 = uVar3 & 0xfffff | 0x80000;
  uVar4 = DAT_00001824;
LAB_000015ea:
  return CONCAT44(uVar4 << 0x14 | uVar3 | iVar8 << 0x1f,uVar1);
}


