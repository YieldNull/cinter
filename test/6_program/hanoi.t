 /* Element conf[d] gives the current position of disk d. */
int[10] conf;

void move(int d, int t) {
    /* move disk d to peg t */
    conf[d] = t;
    write(d);
    write(t);
    write(1.1);
    return;
}

void hanoi(int h, int t) {
    if (h > 0) {
        int tmp=h-1;
        int f = conf[tmp];
        if (f <> t) {
            int r = 3 - f - t ;
            hanoi(h-1, r);
            move(h-1, t);
        }
        hanoi(h-1, t);
    }
    return;
}

void main(){
	int i=0;
	while(i<10){
		conf[i]=1;
		i=i+1;
	}
    hanoi(10,1);
    return;
}
