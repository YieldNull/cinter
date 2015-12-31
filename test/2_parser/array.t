int[5] a={1,2,3};

int i;
int j;

void main(){
	j=0;
	while(i<5){
   		a[i]=j+1;
    	j=j+i;
    	write(a[i]);
		i=i+1;
	}
	return;
}