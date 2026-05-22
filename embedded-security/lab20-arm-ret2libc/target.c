#include <stdio.h>
#include <unistd.h>

// Gadgets Thumb ARM32 — équivalent ARM du ret2syscall (Lab10)
__asm__(".section .text\n"
        ".thumb\n"
        ".global pop_r7_pc\n.thumb_func\npop_r7_pc:\n\tpop {r7, pc}\n"
        ".global pop_r0_pc\n.thumb_func\npop_r0_pc:\n\tpop {r0, pc}\n"
        ".global pop_r1_r2_pc\n.thumb_func\npop_r1_r2_pc:\n\tpop {r1, r2, pc}\n"
        ".global do_svc\n.thumb_func\ndo_svc:\n\tsvc #0\n\tnop\n");

const char binsh[] = "/bin/sh";
const char arg_i[] = "-i";
const char* sh_argv[] = {binsh, arg_i, NULL};

void vulnerable() {
    char buffer[64];
    puts("Input : ");
    read(0, buffer, 200);
}

int main() { vulnerable(); return 0; }
