// function and variable redefined conflict

int foo(){
    return 0;
}

void main(){
    real foo; // foo is redefined
    return;
}