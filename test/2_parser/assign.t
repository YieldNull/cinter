// This is a test for assign

int a;
real[3] b,d;

int foo(){
	return 1;
}
void main(){
	a=foo();

	b[0]=1.5;
	b[1]=a;
	b[2]=4.0;

	d=(b[0])+(b[3]*a)/5;
	return;
}