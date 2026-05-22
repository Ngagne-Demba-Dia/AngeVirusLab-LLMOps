#include <stdio.h>
#include <unistd.h>

// Gadgets dans .text (avant les globals)
__asm__(".section .text\n"
        ".global pop_rax\npop_rax:\n\tpop %rax\n\tret\n"
        ".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n"
        ".global pop_rsi\npop_rsi:\n\tpop %rsi\n\tret\n"
        ".global pop_rdx\npop_rdx:\n\tpop %rdx\n\tret\n"
        ".global do_syscall\ndo_syscall:\n\tsyscall\n\tret\n");

const char binsh[] = "/bin/sh";
const char arg_i[] = "-i";
const char* sh_argv[] = {binsh, arg_i, NULL};

void vulnerable() {
    char buffer[64];

    // Affiche les identifiants avant exploitation
    printf("uid=%d euid=%d gid=%d egid=%d\n",
           getuid(), geteuid(), getgid(), getegid());
    printf("Input : ");
    fflush(stdout);
    read(0, buffer, 200);     // overflow volontaire
}

int main() {
    vulnerable();
    return 0;
}
