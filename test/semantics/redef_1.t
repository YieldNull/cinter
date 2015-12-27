// variable and variable redefined conflict

int a;

void main(){
    int b;
    if (1>0){
	    int a; // a is redefined
	}
	return;
}