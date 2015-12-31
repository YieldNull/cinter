// assign type mismatch
// in a assign expression, each side should own the same data type

void main(){
    int a;
    a=1.3; // a is `int` while 1.3 is `real`
    return ;
}