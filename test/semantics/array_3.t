// an array name can neither be a left value nor a right value.

void main(){
    int[2] a;
    int b;
    b=2+a;  // index missing,using like b=2+a[0]
    return 0;
}