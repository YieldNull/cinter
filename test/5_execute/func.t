// test function call

int a;

int add(int a,int b){
    return a+b;
}

real divide(real a,real b){
    return a/b;
}

void print_int(int a){
    write(a);
    return;
}

void print_real(real a){
    write(a);
    return;
}

void main(){
    a=9;
    int b;
    b=10;

    a=add(a,b);
    print_int(a);

    real c,d;
    c=10.0;d=2.0;

    c=divide(c,d);
    print_real(c);

    return;
}