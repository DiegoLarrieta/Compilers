package main

import (
	"fmt"
	"io"
	"os"
	"regexp"
	"strconv"
)

// lexer implementa la interfaz calcLexer que exige el parser generado
// por goyacc: Lex(*calcSymType) int y Error(string).
type lexer struct {
	src   string
	pos   int
	linea int
	nl    bool // hubo un '\n' pendiente de contar
}

// Cada token se reconoce con una expresión regular anclada al inicio (\A),
// igual que las reglas de un archivo .l de Flex. El orden importa.
var (
	reEspacio = regexp.MustCompile(`\A([ \t]+|#[^\n]*)`)
	reNumero  = regexp.MustCompile(`\A[0-9]+(\.[0-9]+)?`)
	reIdentif = regexp.MustCompile(`\A[a-zA-Z_][a-zA-Z0-9_]*`)
)

func (l *lexer) Lex(lval *calcSymType) int {
	// La línea se incrementa hasta pedir el token siguiente al '\n', porque el
	// parser lee el '\n' como lookahead antes de ejecutar la acción de la línea.
	if l.nl {
		l.linea++
		l.nl = false
	}
	for {
		resto := l.src[l.pos:]
		if resto == "" {
			return 0 // fin de entrada
		}
		if m := reEspacio.FindString(resto); m != "" {
			l.pos += len(m)
			continue
		}
		if m := reNumero.FindString(resto); m != "" {
			l.pos += len(m)
			lval.num, _ = strconv.ParseFloat(m, 64)
			return NUM
		}
		if m := reIdentif.FindString(resto); m != "" {
			l.pos += len(m)
			lval.id = m
			return ID
		}
		c := resto[0]
		l.pos++
		switch c {
		case '\n':
			l.nl = true
			return int(c)
		case '+', '-', '*', '/', '^', '(', ')', '=':
			return int(c)
		default:
			l.Error(fmt.Sprintf("carácter inválido '%c'", c))
		}
	}
}

func (l *lexer) Error(s string) {
	fmt.Printf("línea %d: %s\n", l.linea, s)
}

func main() {
	datos, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	calcParse(&lexer{src: string(datos), linea: 1})
}
