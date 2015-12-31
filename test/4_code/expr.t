// test expression

int foo(){
	return 2;
}
void main(){
    int a;
    a=9;

    int b;
    b=(1-foo())/(foo())*a+(1/a)*foo();
	 write(b);
    return ;
}