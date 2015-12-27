// expression mismatch
// in an expression, all the factor should own the same data type

void main(){
    int a;
    a=1+1.3;// 1 is `int`, while 1.3 is `real`
    return;
}