/*-
 * Copyright (c) 1990 The Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms are permitted
 * provided that the above copyright notice and this paragraph are
 * duplicated in all such forms and that any documentation,
 * and/or other materials related to such
 * distribution and use acknowledge that the software was developed
 * by the University of California, Berkeley.  The name of the
 * University may not be used to endorse or promote products derived
 * from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
 */
/*
 * Copyright (c) 2012-2014 ARM Ltd
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the company may not be used to endorse or promote
 *    products derived from this software without specific prior written
 *    permission.
 *
 * THIS SOFTWARE IS PROVIDED BY ARM LTD ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL ARM LTD BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
 * TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/* Adapted from pinned newlib-4.3.0, see vendor manifest and docs/runtime-scan.md. */
#include "runtime_scan.h"
#include "runtime_stdio.h"
#include "runtime_support.h"
#include <stdint.h>
#include <stddef.h>
_Static_assert(sizeof(void*)==4,"target ARM32 only");
_Static_assert(sizeof(syscon_rt_file)==104,"target FILE size");
_Static_assert(offsetof(syscon_rt_file,_flags)==12,"syscon_rt_file flags ABI");
_Static_assert(offsetof(syscon_rt_file,_bf)==16,"syscon_rt_file buffer ABI");
_Static_assert(offsetof(syscon_rt_file,_ub)==52,"syscon_rt_file pushback ABI");
_Static_assert(offsetof(syscon_rt_file,_ubuf)==68,"syscon_rt_file inline pushback ABI");
_Static_assert(offsetof(struct syscon_scan_state,pfn_ungetc)==380,"scan state ABI");
_Static_assert(offsetof(struct syscon_scan_state,pfn_refill)==384,"scan state ABI");
static int scan_space(int c){return ((const unsigned char*)0xe127)[(unsigned char)c]&8;}
static void *scan_memchr(const void *s,int c,size_t n){const unsigned char*p=s;while(n--){if(*p==(unsigned char)c)return(void*)p;p++;}return 0;}
static int scan_refill(struct _reent*r,syscon_rt_file*f){return syscon_rt_ssrefill_r(r,f);}
static int scan_ungetc(struct _reent*r,int c,syscon_rt_file*f){return syscon_rt_sungetc_r(r,c,f);}
#define isspace scan_space
#define memchr scan_memchr
#define _scan_data_t syscon_scan_state
#define _scanf_chars syscon_scan_chars
#define _scanf_i syscon_scan_integer
#define __sccl syscon_scan_sccl
#define _strtol_r syscon_rt_strtol_r
#define _strtoul_r syscon_rt_strtoul_r
#define _ungetc_r scan_ungetc
#define __srefill_r scan_refill
#define _newlib_flockfile_start(x)
#define _newlib_flockfile_exit(x)
#define _newlib_flockfile_end(x)
#define BUF 350
#define GET_ARG(n,ap,type) va_arg(ap,type)
#define u_char unsigned char
#define u_long unsigned long
#define to_digit(c) ((c)-'0')
#define is_digit(c) ((unsigned)to_digit(c)<=9)
#define SHORT 1
#define LONG 2
#define SUPPRESS 0x10
#define POINTER 0x20
#define NOSKIP 0x40
#define NDIGITS 0x100
#define PFXOK 0x200
#define NZDIGITS 0x400
#define NNZDIGITS 0x800
#define CT_CHAR 0
#define CT_CCL 1
#define CT_STRING 2
#define CT_INT 3
#define CT_UINT 4
#define CT_FLOAT 5
#define MATCH_FAILURE 1
#define INPUT_FAILURE 2
#define FLOATING_POINT

u_char *
__sccl (register char *tab,
       register const u_char *fmt)
{
  register int c, n, v;

  /* first `clear' the whole table */
  c = *fmt++;			/* first char hat => negated scanset */
  if (c == '^')
    {
      v = 1;			/* default => accept */
      c = *fmt++;		/* get new first char */
    }
  else
    v = 0;			/* default => reject */
  /* should probably use memset here */
  for (n = 0; n < 256; n++)
    tab[n] = v;
  if (c == 0)
    return (u_char *)(fmt - 1);		/* format ended before closing ] */

  /*
   * Now set the entries corresponding to the actual scanset to the
   * opposite of the above.
   *
   * The first character may be ']' (or '-') without being special; the
   * last character may be '-'.
   */

  v = 1 - v;
  for (;;)
    {
      tab[c] = v;		/* take character c */
    doswitch:
      n = *fmt++;		/* and examine the next */
      switch (n)
	{

	case 0:		/* format ended too soon */
	  return (u_char *)(fmt - 1);

	case '-':
	  /*
	   * A scanset of the form [01+-] is defined as `the digit 0, the
	   * digit 1, the character +, the character -', but the effect of a
	   * scanset such as [a-zA-Z0-9] is implementation defined.  The V7
	   * Unix scanf treats `a-z' as `the letters a through z', but treats
	   * `a-a' as `the letter a, the character -, and the letter a'.
	   *
	   * For compatibility, the `-' is not considerd to define a range if
	   * the character following it is either a close bracket (required by
	   * ANSI) or is not numerically greater than the character we just
	   * stored in the table (c).
	   */
	  n = *fmt;
	  if (n == ']' || n < c)
	    {
	      c = '-';
	      break;		/* resume the for(;;) */
	    }
	  fmt++;
	  do
	    {			/* fill in the range */
	      tab[++c] = v;
	    }
	  while (c < n);
#if 1			/* XXX another disgusting compatibility hack */
	  /*
	   * Alas, the V7 Unix scanf also treats formats such
	   * as [a-c-e] as `the letters a through e'. This too
	   * is permitted by the standard....
	   */
	  goto doswitch;
#else
	  c = *fmt++;
	  if (c == 0)
	    return (u_char *)(fmt - 1);
	  if (c == ']')
	    return (u_char *)fmt;
#endif

	  break;


	case ']':		/* end of scanset */
	  return (u_char *)fmt;

	default:		/* just another character */
	  c = n;
	  break;
	}
    }
  /* NOTREACHED */
}

int
_scanf_chars (struct _reent *rptr,
	      struct _scan_data_t *pdata,
	      syscon_rt_file *fp, va_list *ap)
{
  int n;
  char *p = NULL;

  if (pdata->width == 0)
    pdata->width = (pdata->code == CT_CHAR) ? 1 : (size_t)~0;

  n = 0;
  if ((pdata->flags & SUPPRESS) == 0)
    p = GET_ARG (N, *ap, char *);

  /* It's impossible to have EOF when we get here.  */
  while ((pdata->code == CT_CHAR)
	 || (pdata->code == CT_CCL && pdata->ccltab[*fp->_p])
	 || (pdata->code == CT_STRING && !isspace (*fp->_p)))
    {
      n++;
      if ((pdata->flags & SUPPRESS) == 0)
	*p++ = *fp->_p;
	
      fp->_r--, fp->_p++;
      if (--pdata->width == 0)
	break;

      if ((fp->_r <= 0 && pdata->pfn_refill (rptr, fp)))
	break;
    }
  /* For CT_CHAR, it is impossible to have input_failure(n == 0) here.
     For CT_CCL, it is impossible to have input_failure here.
     For CT_STRING, it is possible to have empty string.  */
  if (n == 0 && pdata->code == CT_CCL)
    return MATCH_FAILURE;

  if ((pdata->flags & SUPPRESS) == 0)
    {
      pdata->nassigned++;
      if (pdata->code != CT_CHAR)
	*p = 0;
    }
  pdata->nread += n;
  return 0;
}
int
_scanf_i (struct _reent *rptr,
	  struct _scan_data_t *pdata,
	  syscon_rt_file *fp, va_list *ap)
{
#define CCFN_PARAMS	(struct _reent *, const char *, char **, int)
  /* Conversion function (strtol/strtoul).  */
  
  char *p = NULL;
  int n;
  char *xdigits = "A-Fa-f8901234567]";
  char *prefix_chars[3] = {"+-", "00", "xX"};

  /* Scan an integer as if by strtol/strtoul.  */
  unsigned width_left = 0;
  int skips = 0;


#ifdef hardway
  if (pdata->width == 0 || pdata->width > BUF - 1)
#else
  /* size_t is unsigned, hence this optimisation.  */
  if (pdata->width - 1 > BUF - 2)
#endif
    {
      width_left = pdata->width - (BUF - 1);
      pdata->width = BUF - 1;
    }
  p = pdata->buf;
  pdata->flags |= NDIGITS | NZDIGITS | NNZDIGITS;

  /* Process [sign] [0] [xX] prefixes sequently.  */
  for (n = 0; n < 3; n++)
    {
      if (!memchr (prefix_chars[n], *fp->_p, 2))
	continue;

      if (n == 1)
	{
	  if (pdata->base == 0)
	    {
	      pdata->base = 8;
	      pdata->flags |= PFXOK;
	    }
	  pdata->flags &= ~(NZDIGITS | NDIGITS);
	}
      else if (n == 2)
	{
	  if ((pdata->flags & (PFXOK | NZDIGITS)) != PFXOK)
	    continue;
	  pdata->base = 16;

	  /* We must reset the NZDIGITS and NDIGITS
	     flags that would have been unset by seeing
	     the zero that preceded the X or x.

	     ??? It seems unnecessary to reset the NZDIGITS.  */
	  pdata->flags |= NDIGITS;
	}
      if (pdata->width-- > 0)
	{
	  *p++ = *fp->_p++;
	  fp->_r--;
	  if ((fp->_r <= 0 && pdata->pfn_refill (rptr, fp)))
	    goto match_end;
	}
    }

  if (pdata->base == 0)
    pdata->base = 10;

  /* The check is un-necessary if xdigits points to exactly the string:
     "A-Fa-f8901234567]".  The code is kept only for reading's sake.  */
#if 0
  if (pdata->base != 16)
#endif
  xdigits = xdigits + 16 - pdata->base;

  /* Initilize ccltab according to pdata->base.  */
  __sccl (pdata->ccltab, (unsigned char *) xdigits);
  for (; pdata->width; pdata->width--)
    {
      n = *fp->_p;
      if (pdata->ccltab[n] == 0)
	break;
      else if (n == '0' && (pdata->flags & NNZDIGITS))
	{
	  ++skips;
	  if (width_left)
	    {
	      width_left--;
	      pdata->width++;
	    }
	  goto skip;
	}
      pdata->flags &= ~(NDIGITS | NNZDIGITS);
      /* Char is legal: store it and look at the next.  */
      *p++ = *fp->_p;
skip:
      if (--fp->_r > 0)
	fp->_p++;
      else if (pdata->pfn_refill (rptr, fp))
	/* "EOF".  */
	break;
    }
  /* If we had only a sign, it is no good; push back the sign.
     If the number ends in `x', it was [sign] '0' 'x', so push back
     the x and treat it as [sign] '0'.
     Use of ungetc here and below assumes ASCII encoding; we are only
     pushing back 7-bit characters, so casting to unsigned char is
     not necessary.  */
match_end:
  if (pdata->flags & NDIGITS)
    {
      if (p > pdata->buf)
	pdata->pfn_ungetc (rptr, *--p, fp); /* "[-+xX]".  */

      if (p == pdata->buf)
	return MATCH_FAILURE;
    }
  if ((pdata->flags & SUPPRESS) == 0)
    {
      u_long ul;
      *p = 0;
      ul = pdata->code == CT_INT ? (uint32_t)syscon_rt_strtol_r(rptr,pdata->buf,0,pdata->base) : syscon_rt_strtoul_r(rptr,pdata->buf,0,pdata->base);
      if (pdata->flags & POINTER)
	*GET_ARG (N, *ap, void **) = (void *) (uintptr_t) ul;
      else if (pdata->flags & SHORT)
	*GET_ARG (N, *ap, short *) = ul;
      else if (pdata->flags & LONG)
	*GET_ARG (N, *ap, long *) = ul;
      else
	*GET_ARG (N, *ap, int *) = ul;
      
      pdata->nassigned++;
    }
  pdata->nread += p - pdata->buf + skips;
  return 0;
}


int
syscon_rt_vfscanf (struct _reent *rptr,
       register syscon_rt_file *fp,
       char const *fmt0,
       va_list ap)
{
  register u_char *fmt = (u_char *) fmt0;
  register int c;		/* Character from format, or conversion.  */
  register char *p;		/* Points into all kinds of strings.  */
  char ccltab[256];		/* Character class table for %[...].  */
  va_list ap_copy;

  int ret;
  char *cp;

  struct _scan_data_t scan_data;


  _newlib_flockfile_start (fp);

  scan_data.nassigned = 0;
  scan_data.nread = 0;
  scan_data.ccltab = ccltab;
  scan_data.pfn_ungetc = _ungetc_r;
  scan_data.pfn_refill = __srefill_r;

  /* GCC PR 14577 at https://gcc.gnu.org/bugzilla/show_bug.cgi?id=14557 */
  va_copy (ap_copy, ap);

  for (;;)
    {
      if (*fmt == 0)
	goto all_done;

      if (isspace (*fmt))
	{
	  while ((fp->_r > 0 || !scan_data.pfn_refill(rptr, fp))
		 && isspace (*fp->_p))
	    {
	      scan_data.nread++;
	      fp->_r--;
	      fp->_p++;
	    }
	  fmt++;
	  continue;
	}
      if ((c = *fmt++) != '%')
	goto literal;

      scan_data.width = 0;
      scan_data.flags = 0;

      if (*fmt == '*')
	{
	  scan_data.flags |= SUPPRESS;
	  fmt++;
	}

      for (; is_digit (*fmt); fmt++)
	scan_data.width = 10 * scan_data.width + to_digit (*fmt);

      /* The length modifiers.  */
      p = "hlL";
      if ((cp = memchr (p, *fmt, 3)) != NULL) {
	scan_data.flags |= (SHORT << (cp - p));
	fmt++;
      }

      /* Switch on the format.  continue if done; break once format
	 type is derived.  */
      c = *fmt++;
      switch (c)
	{
	case '%':
	literal:
	  if ((fp->_r <= 0 && scan_data.pfn_refill(rptr, fp)))
	    goto input_failure;
	  if (*fp->_p != c)
	    goto match_failure;
	  fp->_r--, fp->_p++;
	  scan_data.nread++;
	  continue;

	case 'p':
	  scan_data.flags |= POINTER;
          /* fall through */
	case 'x':
	case 'X':
	  scan_data.flags |= PFXOK;
	  scan_data.base = 16;
	  goto number;
	case 'd':
	case 'u':
	  scan_data.base = 10;
	  goto number;
	case 'i':
	  scan_data.base = 0;
	  goto number;
	case 'o':
	  scan_data.base = 8;
	number:
	  scan_data.code = (c < 'o') ? CT_INT : CT_UINT;
	  break;

	case '[':
	  fmt = (u_char *) __sccl (ccltab, (unsigned char *) fmt);
	  scan_data.flags |= NOSKIP;
	  scan_data.code = CT_CCL;
	  break;
	case 'c':
	  scan_data.flags |= NOSKIP;
	  scan_data.code = CT_CHAR;
	  break;
	case 's':
	  scan_data.code = CT_STRING;
	  break;

	case 'n':
	  if (scan_data.flags & SUPPRESS)	/* ???  */
	    continue;

	  if (scan_data.flags & SHORT)
	    *GET_ARG (N, ap_copy, short *) = scan_data.nread;
	  else if (scan_data.flags & LONG)
	    *GET_ARG (N, ap_copy, long *) = scan_data.nread;
	  else
	    *GET_ARG (N, ap_copy, int *) = scan_data.nread;

	  continue;

	/* Disgusting backwards compatibility hacks.	XXX.  */
	case '\0':		/* compat.  */
	  _newlib_flockfile_exit (fp);
	  va_end (ap_copy);
	  return EOF;

#ifdef FLOATING_POINT
	case 'e': case 'E':
	case 'f': case 'F':
	case 'g': case 'G':
	  scan_data.code = CT_FLOAT;
	  break;
#endif
	default:		/* compat.  */
	  scan_data.code = CT_INT;
	  scan_data.base = 10;
	  break;
	}

      /* We have a conversion that requires input.  */
      if ((fp->_r <= 0 && scan_data.pfn_refill (rptr, fp)))
	goto input_failure;

      /* Consume leading white space, except for formats that
	 suppress this.  */
      if ((scan_data.flags & NOSKIP) == 0)
	{
	  while (isspace (*fp->_p))
	    {
	      scan_data.nread++;
	      if (--fp->_r > 0)
		fp->_p++;
	      else if (scan_data.pfn_refill (rptr, fp))
		goto input_failure;
	    }
	  /* Note that there is at least one character in the
	     buffer, so conversions that do not set NOSKIP ca
	     no longer result in an input failure.  */
	}
      ret = 0;
      if (scan_data.code < CT_INT)
	ret = _scanf_chars (rptr, &scan_data, fp, &ap_copy);
      else if (scan_data.code < CT_FLOAT)
	ret = _scanf_i (rptr, &scan_data, fp, &ap_copy);
#ifdef FLOATING_POINT
      /* Original weak _scanf_float is NULL: no conversion or argument consumption. */
#endif

      if (ret == MATCH_FAILURE)
	goto match_failure;
      else if (ret == INPUT_FAILURE)
	goto input_failure;
    }
input_failure:
  /* On read failure, return EOF failure regardless of matches; errno
     should have been set prior to here.  On EOF failure (including
     invalid format string), return EOF if no matches yet, else number
     of matches made prior to failure.  */
  _newlib_flockfile_exit (fp);
  va_end (ap_copy);
  return scan_data.nassigned && !(fp->_flags & __SERR) ? scan_data.nassigned
						       : EOF;
match_failure:
all_done:
  /* Return number of matches, which can be 0 on match failure.  */
  _newlib_flockfile_end (fp);
  va_end (ap_copy);
  return scan_data.nassigned;
}
