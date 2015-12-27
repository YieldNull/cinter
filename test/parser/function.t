// Test function


// function define test
void void_test(void){
	return;
}

int void_test2(){
	return 1;
}

int normal_test(int a){
	return b+a;
}

void multi_args_test(int a,real b){

	return;
}

int main(){
	int a;
	a=0;
	int[3] arr;

	void_test();			// call param `Empty` test
	a=void_test2(void);	// call param `void` test

	normal_test(a+3/9-4*arr[1]);	//call param `expression`test
	multi_args_test(1,2.0);

	return a+3/9-4*arr[1]; //return `expression` test
}
