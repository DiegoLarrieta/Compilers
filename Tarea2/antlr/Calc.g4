// Calculadora en ANTLR 4: lexer y parser en un solo archivo.
// La precedencia la da el orden de las alternativas (la primera liga más fuerte).
grammar Calc;

entrada : linea* EOF ;

linea   : expr NL                  # lineaExpr
        | NL                       # lineaVacia
        ;

expr    : <assoc=right> expr '^' expr   # potencia
        | '-' expr                      # negativo
        | expr op=('*'|'/') expr        # mulDiv
        | expr op=('+'|'-') expr        # sumaResta
        | <assoc=right> ID '=' expr     # asignacion
        | NUM                           # numero
        | ID                            # variable
        | '(' expr ')'                  # parentesis
        ;

NUM     : [0-9]+ ('.' [0-9]+)? ;
ID      : [a-zA-Z_] [a-zA-Z0-9_]* ;
NL      : '\r'? '\n' ;
ESPACIO : [ \t]+ -> skip ;
COMENT  : '#' ~[\r\n]* -> skip ;
