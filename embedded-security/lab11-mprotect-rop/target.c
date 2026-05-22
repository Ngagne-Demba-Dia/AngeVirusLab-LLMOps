#include <stdio.h>
#include <unistd.h>

// Gadgets dans .text (avant les globals — lecon Lab10)
__asm__(".section .text\n"
        ".global pop_rax\npop_rax:\n\tpop %rax\n\tret\n"
        ".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n"
        ".global pop_rsi\npop_rsi:\n\tpop %rsi\n\tret\n"
        ".global pop_rdx\npop_rdx:\n\tpop %rdx\n\tret\n"
        ".global do_syscall\ndo_syscall:\n\tsyscall\n\tret\n");

void vulnerable() {
    char buffer[256];

    // Leak adresse du buffer : permet de calculer ou sauter apres mprotect
    printf("buffer @ %p\n", buffer);
    fflush(stdout);
    read(0, buffer, 512);      // overflow volontaire
}

int main() {
    vulnerable();
    return 0;
}
