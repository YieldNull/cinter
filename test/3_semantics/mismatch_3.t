// compare mismatch
// both side of compare should own the same data type

real demo(){
	return 1.3;
}

void main(){
    if(demo()>1){ // 1.3 is `real`, while 1 is `int`

    }
    return ;
}