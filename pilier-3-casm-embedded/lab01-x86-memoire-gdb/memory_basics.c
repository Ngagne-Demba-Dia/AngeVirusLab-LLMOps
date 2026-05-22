#include <stdio.h>
#include <stdlib.h>

void demo_stack() {
    int a = 10;
    int b = 20;
    int *ptr = &a;
    printf("=== STACK ===\n");
    printf("a = %d, adresse de a = %p\n", a, &a);
    printf("b = %d, adresse de b = %p\n", b, &b);
    printf("ptr pointe sur : %p, valeur = %d\n", ptr, *ptr);
    *ptr = 99;
    printf("Apres *ptr = 99 : a = %d\n", a);
}

void demo_heap() {
    int *tab = malloc(5 * sizeof(int));
    printf("\n=== HEAP ===\n");
    for (int i = 0; i < 5; i++) tab[i] = i * 10;
    for (int i = 0; i < 5; i++)
        printf("tab[%d] = %d, adresse = %p\n", i, tab[i], &tab[i]);
    free(tab);
}

void demo_segfault() {
    printf("\n=== SEGFAULT ===\n");
    int *null_ptr = NULL;
    printf("Valeur : %d\n", *null_ptr);  // CRASH ICI
}

int main() {
    demo_stack();
    demo_heap();
    demo_segfault();
    return 0;
}
