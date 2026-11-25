%{
// Parser de la calculadora: gramática LALR(1) con acciones semánticas en Go.
package main

import (
	"fmt"
	"math"
)

// Tabla de símbolos: guarda el valor de cada variable.
var vars = map[string]float64{}
%}

%union {
	num float64
	id  string
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
        | expr '\n'        { fmt.Printf("= %g\n", $1) }
        | error '\n'
        ;

expr    : NUM                   { $$ = $1 }
        | ID                    { $$ = vars[$1] }
        | ID '=' expr           { vars[$1] = $3; $$ = $3 }
        | expr '+' expr         { $$ = $1 + $3 }
        | expr '-' expr         { $$ = $1 - $3 }
        | expr '*' expr         { $$ = $1 * $3 }
        | expr '/' expr         {
                                  if $3 == 0 {
                                      calclex.(*lexer).Error("división entre cero")
                                      $$ = 0
                                  } else {
                                      $$ = $1 / $3
                                  }
                                }
        | expr '^' expr         { $$ = math.Pow($1, $3) }
        | '-' expr %prec UMENOS { $$ = -$2 }
        | '(' expr ')'          { $$ = $2 }
        ;

%%
