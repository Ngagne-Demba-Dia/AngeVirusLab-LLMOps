#include <stdio.h>
#include <unistd.h>

int main() {
    printf("[*] PID cible : %d\n", getpid());
    fflush(stdout);
    while (1) {
        printf("En vie...\n");
        fflush(stdout);
        sleep(2);
    }
    return 0;
}
