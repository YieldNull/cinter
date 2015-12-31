// function and function redefined conflict

void foo(){
    return ;
}

int foo(){ // foo is redefined
    return 0;
}

void main(){

    return;
}