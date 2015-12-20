int[5] a;

int i;
int j;

int main(){
	j=9;
	while(i<5){
   		a[i]=j+1;
    	j=j+i;
    	write(a[i]);
	}
}