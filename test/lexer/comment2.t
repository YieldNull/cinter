/**
 * This is a test for multiple line comments
 */
int i/*~ /*Ha*ha/* ~*/=0;

/*
Below is a nest comment, which is invalid.
But at lexical analysis state, it's valid,
which can be recognized as "<ID: 'ccc'> <TIMES: '*'> <DIVIDE: '/'>"
*/

/*aaa/*bbb*/ccc*/