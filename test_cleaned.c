#include <stdio.h>
#include <stdbool.h>
int factorial(int n) {
int result = 1;
for (int i = 1; i <= n; i++) {
result = result * i;
}
return result;
}
bool is_even(int value) {
return value % 2 == 0;
}
int main(void) {
int a = 5;
int b = 3;
int sum = 0;
int difference = 0;
int product = 0;
int quotient = 0;
int counter = 0;
int fact = 0;
bool check = false;
sum = a + b;
difference = a - b;
product = a * b;
quotient = a / b;
fact = factorial(a);
check = is_even(sum) && (product > difference);
if (check) {
printf("Condition is true\n");
} else {
printf("Condition is false\n");
}
while (counter < 3) {
printf("counter = %d\n", counter);
counter = counter + 1;
}
for (int i = 0; i < 5; i++) {
printf("i = %d\n", i);
}
printf("sum = %d\n", sum);
printf("difference = %d\n", difference);
printf("product = %d\n", product);
printf("quotient = %d\n", quotient);
printf("factorial(%d) = %d\n", a, fact);
return 0;
}
