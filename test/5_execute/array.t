// test array

int[3] arr;

void main(){
    int a;
    a=1;

    arr[0]=1;   // arr[0]:1
    arr[a]=2;   // arr[1]:2

    a=arr[1];
    arr[2]=a+1; // arr[2]:3

    int i;
    i=0;
    while(i<3){
        write(arr[i]);
        i=i+1;
    }
    return;
}