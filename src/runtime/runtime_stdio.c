#include "runtime_stdio.h"
#include "runtime_support.h"
#include "runtime_heap.h"
#include "runtime_memory.h"
#include <stdint.h>
#define P(a) ((uint32_t *)(uintptr_t)(uint32_t)(a))
#define U(p) ((uint32_t)(uintptr_t)(p))
uint32_t syscon_rt_strtoul_r(void *reent, const char *text, char **end, int base)
{
    const uint8_t *s = (const uint8_t *)text;
    uint32_t c;
    do {
        c = *s++;
    } while (syscon_rt_ctype(c) & SYSCON_CTYPE_SPACE);
    unsigned negative = 0;
    if (c == '-') {
        negative = 1;
        c = *s++;
    } else if (c == '+')
        c = *s++;
    if ((base == 0 || base == 16) && c == '0') {
        if ((*s & 0xdf) == 'X') {
            c = s[1];
            s += 2;
            base = 16;
        } else if (!base)
            base = 8;
    } else if (!base)
        base = 10;
    uint32_t divisor = (uint32_t)base;
    /* ARM divide-by-zero helper returns quotient0. Base0 is resolved above. */
    uint32_t cutoff = divisor ? UINT32_MAX / divisor : 0;
    uint32_t cutlim = divisor ? UINT32_MAX % divisor : UINT32_MAX;
    uint32_t value = 0;
    int any = 0;
    for (;; c = *s++) {
        uint32_t digit = c - '0';
        if (digit > 9) {
            if (c - 'A' < 26)
                digit = c - 'A' + 10;
            else if (c - 'a' < 26)
                digit = c - 'a' + 10;
            else
                break;
        }
        if (base <= (int32_t)digit)
            break;
        if (any < 0 || value > cutoff || (value == cutoff && digit > cutlim))
            any = -1;
        else {
            any = 1;
            value = value * divisor + digit;
        }
    }
    if (any < 0) {
        value = UINT32_MAX;
        *(uint32_t *)reent = 34;
    } else if (negative)
        value = 0 - value;
    if (end)
        *end = (char *)(any ? s - 1 : (const uint8_t *)text);
    return value;
}
extern void *syscon_rt_memmove(void *, const void *, uint32_t);
static uint16_t *flags(void *stream)
{
    return (uint16_t *)((uint8_t *)stream + 12);
}
int syscon_rt_swrite(void *reent, void *stream, const char *data, uint32_t length)
{
    uint32_t *s = stream, n = length;
    if (s[2] <= length) {
        n = s[2];
        if (*flags(s) & 0x480) {
            uint32_t position = s[0] - s[4], needed = length + 1 + position;
            uint32_t grown = (uint32_t)((int32_t)(s[5] * 3) / 2);
            if (grown < needed)
                grown = needed;
            void *memory;
            if (*flags(s) & 0x400) {
                memory = syscon_rt_malloc_r(reent, grown);
                if (!memory)
                    goto failed;
                syscon_rt_memcpy(memory, (void *)(uintptr_t)s[4], position);
                *flags(s) = (*flags(s) & 0xfb7f) | 0x80;
            } else {
                memory = syscon_rt_realloc_r(reent, (void *)(uintptr_t)s[4], grown);
                if (!memory) {
                    syscon_rt_free_r(reent, (void *)(uintptr_t)s[4]);
                    goto failed;
                }
            }
            s[4] = U(memory);
            s[0] = U(memory) + position;
            s[5] = grown;
            s[2] = grown - position;
            n = length;
        }
    }
    syscon_rt_memmove((void *)(uintptr_t)s[0], data, n);
    s[2] -= n;
    s[0] += n;
    return 0;
failed:
    *(uint32_t *)reent = 12;
    *flags(s) |= 0x40;
    return -1;
}
int syscon_rt_submore(void *reent, void *stream)
{
    uint32_t *s = stream, base = s[13];
    if (base == U(s) + 68) {
        uint8_t *memory = syscon_rt_malloc_r(reent, 1024);
        if (!memory)
            return -1;
        s[13] = U(memory);
        s[14] = 1024;
        memory[1023] = ((uint8_t *)s)[70];
        memory[1022] = ((uint8_t *)s)[69];
        memory[1021] = *(uint8_t *)(uintptr_t)base;
        s[0] = U(memory) + 1021;
    } else {
        uint32_t size = s[14];
        uint8_t *memory = syscon_rt_realloc_r(reent, (void *)(uintptr_t)base, size * 2);
        if (!memory)
            return -1;
        syscon_rt_memcpy(memory + size, memory, size);
        s[0] = U(memory) + size;
        s[13] = U(memory);
        s[14] = size * 2;
    }
    return 0;
}
int syscon_rt_sungetc_r(void *reent, int input, void *stream)
{
    if (input == -1)
        return -1;
    uint32_t *s = stream, c = (uint8_t)input;
    *flags(s) &= (uint16_t)~0x20;
    uint32_t count = s[1];
    if (!s[13]) {
        uint32_t p = s[0];
        if (s[4] && s[4] < p && *(uint8_t *)(uintptr_t)(p - 1) == c) {
            s[0] = p - 1;
            s[1] = count + 1;
            return (int)c;
        }
        s[16] = count;
        s[13] = U(s) + 68;
        s[14] = 3;
        s[15] = p;
        ((uint8_t *)s)[70] = (uint8_t)input;
        s[0] = U(s) + 70;
        s[1] = 1;
    } else {
        if ((int32_t)s[14] <= (int32_t)count && syscon_rt_submore(reent, s))
            return -1;
        --s[0];
        *(uint8_t *)(uintptr_t)s[0] = (uint8_t)input;
        ++s[1];
    }
    return (int)c;
}
int syscon_rt_ssrefill_r(void *reent, void *stream)
{
    uint32_t *s = stream;
    if (s[13]) {
        if (s[13] != U(s) + 68)
            syscon_rt_free_r(reent, (void *)(uintptr_t)s[13]);
        s[13] = 0;
        s[1] = s[16];
        if (s[16]) {
            s[0] = s[15];
            return 0;
        }
    }
    s[0] = s[4];
    s[1] = 0;
    *flags(s) |= 0x20;
    return -1;
}
int syscon_rt_printf_common(void *reent, void *state, int32_t *real_size, void *stream,
                            syscon_rt_writer write)
{
    uint32_t *s = state;
    uint8_t *bytes = state;
    uint32_t real = (int32_t)s[4] < (int32_t)s[2] ? s[2] : s[4];
    if (bytes[67])
        ++real;
    if (s[0] & 0x20)
        real += 2;
    *real_size = (int32_t)real;
    if (!(s[0] & 6))
        for (uint32_t i = 0; (int32_t)i < (int32_t)(s[3] - real); ++i)
            if (write(reent, stream, (const char *)bytes + 25, 1) == -1)
                return -1;
    unsigned have_sign = bytes[67] != 0, length = have_sign;
    if (s[0] & 0x20) {
        bytes[67 + have_sign] = '0';
        bytes[68 + have_sign] = bytes[69];
        length = have_sign + 2;
    }
    if (write(reent, stream, (const char *)bytes + 67, length) == -1)
        return -1;
    uint32_t pad = 0;
    if ((s[0] & 6) == 4 && (int32_t)(s[3] - real) > 0)
        pad = s[3] - real;
    if ((int32_t)s[4] < (int32_t)s[2])
        pad += s[2] - s[4];
    for (uint32_t i = 0; i != pad; ++i)
        if (write(reent, stream, (const char *)bytes + 26, 1) == -1)
            return -1;
    return 0;
}
static uint32_t next_word(void *arguments)
{
    uint32_t *p = arguments, address = *p;
    *p = address + 4;
    return *P(address);
}
int syscon_rt_printf_integer(void *reent, void *state, void *stream, syscon_rt_writer write,
                             void *arguments)
{
    uint32_t *s = state;
    uint8_t *bytes = state, *sign = bytes + 67, *output = sign;
    uint32_t code = bytes[24], value = 0, radix = 10;
    const char *digits = "0123456789ABCDEF";
    switch (code) {
    case 0:
        s[4] = 0;
        goto emit;
    case 'c':
        bytes[66] = (uint8_t)next_word(arguments);
        goto character;
    case 'd':
    case 'i':
        value = next_word(arguments);
        if (!(s[0] & 0x80) && (s[0] & 0x40))
            value = (uint32_t)(int32_t)(int16_t)value;
        if ((int32_t)value < 0) {
            value = 0 - value;
            *sign = '-';
        }
        radix = 10;
        goto integer;
    case 'n': {
        uint32_t destination = next_word(arguments);
        if ((s[0] & 0x80) || !(s[0] & 0x40))
            *P(destination) = s[5];
        else
            *(uint16_t *)(uintptr_t)destination = (uint16_t)s[5];
        s[4] = 0;
        goto emit;
    }
    case 'o':
    case 'u':
        value = next_word(arguments);
        if (!(s[0] & 0x80) && (s[0] & 0x40))
            value &= 0xffff;
        radix = code == 'o' ? 8 : 10;
        *sign = 0;
        goto integer;
    case 'p':
        s[0] |= 0x20; /* fall through */
    case 'x':
        digits = "0123456789abcdef";
        bytes[69] = 'x';
        goto hexadecimal;
    case 'X':
        bytes[69] = 'X';
    hexadecimal:
        value = next_word(arguments);
        if (!(s[0] & 0x80) && (s[0] & 0x40))
            value &= 0xffff;
        if (s[0] & 1)
            s[0] |= 0x20;
        if (!value)
            s[0] &= ~UINT32_C(0x20);
        radix = 16;
        *sign = 0;
        goto integer;
    case 's': {
        output = (uint8_t *)(uintptr_t)next_word(arguments);
        uint8_t *nul = syscon_rt_memchr(output, 0, s[1]);
        if (nul)
            s[1] = (uint32_t)(nul - output);
        s[4] = s[1];
        *sign = 0;
        goto emit;
    }
    default:
        bytes[66] = (uint8_t)code;
    character:
        output = bytes + 66;
        s[4] = 1;
        *sign = 0;
        goto emit;
    }
integer:
    s[2] = s[1];
    if ((int32_t)s[1] >= 0)
        s[0] &= ~UINT32_C(4);
    if (value || s[1])
        do {
            *--output = (uint8_t)digits[value % radix];
            value /= radix;
        } while (value);
    if (radix == 8 && (s[0] & 1) && (int32_t)s[1] <= (int32_t)s[4])
        *--output = '0';
    s[4] = (uint32_t)(sign - output);
emit:;
    int32_t real_size;
    if (syscon_rt_printf_common(reent, state, &real_size, stream, write) == -1)
        return -1;
    if (write(reent, stream, (const char *)output, s[4]) == -1)
        return -1;
    if (s[0] & 2)
        for (uint32_t i = 0; (int32_t)i < (int32_t)(s[3] - (uint32_t)real_size); ++i)
            if (write(reent, stream, (const char *)bytes + 25, 1) == -1)
                return -1;
    return (int32_t)s[3] < real_size ? real_size : (int32_t)s[3];
}
