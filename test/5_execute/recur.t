int fibonacci(int n){
	 if(n==0){
	    return 0;
    }
    if(n<3){
    	return 1;
	 }
	 
    return fibonacci(n-1)+fibonacci(n-2);
}

void main(){
    int i,r;
    i=0;
    while(i<20){
		r=fibonacci(i);
		write(r);
      i=i+1;
	 }
	return;
}