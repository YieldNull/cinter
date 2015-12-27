// when calling a function, params which are passed must be corresponding to func def

int foo(){
    return 0;
}

void main(){
    foo(1);   // param count mismatch
    return;
}