%{
/* Scanner de la calculadora: convierte caracteres en tokens para Bison. */
#include <stdlib.h>
#include "calc.tab.h"

int linea = 1;
static int nl_pendiente = 0;

/* YY_USER_ACTION se ejecuta antes de cada acción: cuenta el '\n' anterior
   hasta pedir el siguiente token, porque Bison lo lee como lookahead. */
#define YY_USER_ACTION if (nl_pendiente) { linea++; nl_pendiente = 0; }
%}

%option noyywrap

DIGITO  [0-9]
LETRA   [a-zA-Z_]

%%

{DIGITO}+("."{DIGITO}+)?   { yylval.num = atof(yytext); return NUM; }
{LETRA}({LETRA}|{DIGITO})* { yylval.id = yytext[0]; return ID; }
[-+*/^()=]                 { return yytext[0]; }
\n                         { nl_pendiente = 1; return '\n'; }
[ \t]+                     { /* ignorar espacios */ }
"#".*                      { /* ignorar comentarios */ }
.                          { printf("línea %d: carácter inválido '%s'\n", linea, yytext); }

%%
