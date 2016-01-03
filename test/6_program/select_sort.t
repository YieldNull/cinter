int[20] arr={12, 58, 13, 89, 42, 89, 76, 89, 13, 50, 39, 40, 88, 80, 1, 43, 42, 84, 92, 80};

void selection_sort(int len) {
	int i, j, min, temp=0;
	while(i < len - 1){
		min = i;

		j = i + 1;
		while(j<len){
			if (arr[min] > arr[j]){
				min = j;
			}
			j=j+1;
		}
	   	temp = arr[min];
		arr[min] = arr[i];
		arr[i] = temp;
		i=i+1;
	}
	return ;
}

void main(){
    int len=20;
    selection_sort(len);

    int i=0;
	while(i<20){
	    write(arr[i]);
		i=i+1;
	}
	return;
}