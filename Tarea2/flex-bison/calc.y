%{
/* Parser de la calculadora: gramática LALR(1) con acciones semánticas en C. */
#include <stdio.h>
#include <math.h>

int yylex(void);
void yyerror(const char *s);
extern int linea;

double vars[128]; /* tabla de símbolos: una variable por letra inicial */
%}

%union {
    double num;
    char   id;
}

%token <num> NUM
%token <id>  ID
%type  <num> expr

%right '='
%left  '+' '-'
%left  '*' '/'
%right UMENOS
%right '^'

%%

entrada : /* vacío */
        | entrada linea
        ;

linea   : '\n'
        | expr '\n'        { printf("= %g\n", $1); }
        | error '\n'       { yyerrok; }
        ;

expr    : NUM                  { $$ = $1; }
        | ID                   { $$ = vars[(int)$1]; }
        | ID '=' expr          { vars[(int)$1] = $3; $$ = $3; }
        | expr '+' expr        { $$ = $1 + $3; }
        | expr '-' expr        { $$ = $1 - $3; }
        | expr '*' expr        { $$ = $1 * $3; }
        | expr '/' expr        {
                                 if ($3 == 0) { yyerror("división entre cero"); $$ = 0; }
                                 else $$ = $1 / $3;
                               }
        | expr '^' expr        { $$ = pow($1, $3); }
        | '-' expr %prec UMENOS { $$ = -$2; }
        | '(' expr ')'         { $$ = $2; }
        ;

%%

void yyerror(const char *s) {
    printf("línea %d: %s\n", linea, s);
}

int main(void) {
    return yyparse();
}
