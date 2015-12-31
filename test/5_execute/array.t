// test array

int[3] arr={1,2,3};

void main(){
    int a=1;

    arr[0]=1;   // arr[0]:1
    arr[a]=2;   // arr[1]:2

    a=arr[1];
    arr[2]=a+1; // arr[2]:3

    int i=0;
    while(i<3){
        write(arr[i]);
        i=i+1;
    }
    return;
}