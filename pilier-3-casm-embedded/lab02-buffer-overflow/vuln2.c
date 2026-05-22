#include <stdio.h>
#include <unistd.h>

void secret() {
    printf(">>> ACCES SECRET OBTENU ! Bravo AngeVirus <<<\n");
}

void vulnerable() {
    char buffer[64];
    printf("Adresse de secret() : %p\n", secret);
    printf("Entrez votre input : ");
    fflush(stdout);
    read(0, buffer, 200);  // lit des bytes bruts, pas de problème de null
}

int main() {
    vulnerable();
    return 0;
}
