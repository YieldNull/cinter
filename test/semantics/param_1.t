// when calling a function, params which are passed must be corresponding to func def

int foo(int a,real b){
    return 1;
}

void main(){
    foo(1,1);   // param type mismatch
    return;
}