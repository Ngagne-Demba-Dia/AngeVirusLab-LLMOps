#include <stdio.h>
#include <unistd.h>

/*
 * Gadgets MIPSEL inline — architecture MIPS 32-bit little-endian
 * Chaque gadget termine par jr $ra + nop (delay slot obligatoire).
 * Equvalent ARM : pop {r0, pc} → lw $a0, 0($sp); jr $ra; nop
 */
__asm__(
    ".section .text\n"
    ".set    mips32r2\n"
    ".set    noreorder\n"

    ".global gadget_lw_a0_jr_ra\n"
    "gadget_lw_a0_jr_ra:\n"
    "\tlw  $a0, 0($sp)\n"       /* a0 = [sp] = &"/bin/sh"      */
    "\tjr  $ra\n"
    "\taddiu $sp, $sp, 4\n"     /* delay slot : avance sp de 4 */

    ".global gadget_li_a1a2_syscall\n"
    "gadget_li_a1a2_syscall:\n"
    "\tli  $a1, 0\n"            /* a1 = NULL (argv)            */
    "\tli  $a2, 0\n"            /* a2 = NULL (envp)            */
    "\tli  $v0, 4011\n"         /* v0 = SYS_execve (MIPS O32)  */
    "\tsyscall\n"
    "\tnop\n"
);

const char binsh[] = "/bin/sh";

/* Cible ret2win — Lab21 Part 1 */
void win() {
    puts(">>> FLAG : AngeVirus{mips_ra_overflow_controlled} <<<");
}

void vulnerable() {
    char buffer[64];
    printf("win @ %p\n", win);
    fflush(stdout);
    read(0, buffer, 200);
}

int main() {
    vulnerable();
    return 0;
}
