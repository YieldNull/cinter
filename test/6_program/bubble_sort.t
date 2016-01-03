int[20] arr={12, 58, 13, 89, 42, 89, 76, 89, 13, 50, 39, 40, 88, 80, 1, 43, 42, 84, 92, 80};

void swap(int x,int y){
    int tmp=arr[x];
    arr[x]=arr[y];
    arr[y]=tmp;
    return;
}

void bubble_sort(int len) {
	int i, j, temp=0;
	while(i < len - 1){
	    j=0;
	    while( j < len - 1 - i){
	        int t=j + 1;
			if (arr[j] > arr[t]) {
				swap(j,j+1);
			}
		    j=j+1;
		}
		i=i+1;
	}
	return;
}

void main() {
	int len = 20;
	bubble_sort(len);

	int i=0;
	while(i<20){
	    write(arr[i]);
		i=i+1;
	}
	return;
}
