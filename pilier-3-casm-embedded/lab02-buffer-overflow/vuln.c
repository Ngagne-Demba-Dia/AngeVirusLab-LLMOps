#include <stdio.h>
#include <string.h>

void secret() {
    printf(">>> ACCES SECRET OBTENU ! Bravo AngeVirus <<<\n");
}

void vulnerable(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // PAS de vérification de taille → BoF
    printf("Tu as entré : %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <input>\n", argv[0]);
        return 1;
    }
    printf("Adresse de secret() : %p\n", secret);
    vulnerable(argv[1]);
    return 0;
}
