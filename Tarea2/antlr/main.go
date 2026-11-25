package main

import (
	"fmt"
	"math"
	"os"
	"strconv"

	"calc/parser"

	"github.com/antlr4-go/antlr/v4"
)

// evaluador recorre el árbol sintáctico con el patrón Visitor generado por
// ANTLR (-visitor). Aquí vive todo el código propio: la gramática queda limpia.
type evaluador struct {
	parser.BaseCalcVisitor
	vars map[string]float64
}

func (v *evaluador) Visit(t antlr.ParseTree) any { return t.Accept(v) }

func (v *evaluador) VisitEntrada(ctx *parser.EntradaContext) any {
	for _, l := range ctx.AllLinea() {
		v.Visit(l)
	}
	return nil
}

func (v *evaluador) VisitLineaExpr(ctx *parser.LineaExprContext) any {
	fmt.Printf("= %g\n", v.Visit(ctx.Expr()).(float64))
	return nil
}

func (v *evaluador) VisitLineaVacia(ctx *parser.LineaVaciaContext) any { return nil }

func (v *evaluador) VisitNumero(ctx *parser.NumeroContext) any {
	n, _ := strconv.ParseFloat(ctx.GetText(), 64)
	return n
}

func (v *evaluador) VisitVariable(ctx *parser.VariableContext) any {
	return v.vars[ctx.GetText()]
}

func (v *evaluador) VisitAsignacion(ctx *parser.AsignacionContext) any {
	val := v.Visit(ctx.Expr()).(float64)
	v.vars[ctx.ID().GetText()] = val
	return val
}

func (v *evaluador) VisitParentesis(ctx *parser.ParentesisContext) any {
	return v.Visit(ctx.Expr())
}

func (v *evaluador) VisitNegativo(ctx *parser.NegativoContext) any {
	return -v.Visit(ctx.Expr()).(float64)
}

func (v *evaluador) VisitPotencia(ctx *parser.PotenciaContext) any {
	return math.Pow(v.Visit(ctx.Expr(0)).(float64), v.Visit(ctx.Expr(1)).(float64))
}

func (v *evaluador) VisitMulDiv(ctx *parser.MulDivContext) any {
	a, b := v.Visit(ctx.Expr(0)).(float64), v.Visit(ctx.Expr(1)).(float64)
	if ctx.GetOp().GetText() == "*" {
		return a * b
	}
	if b == 0 {
		fmt.Printf("línea %d: división entre cero\n", ctx.GetStart().GetLine())
		return 0.0
	}
	return a / b
}

func (v *evaluador) VisitSumaResta(ctx *parser.SumaRestaContext) any {
	a, b := v.Visit(ctx.Expr(0)).(float64), v.Visit(ctx.Expr(1)).(float64)
	if ctx.GetOp().GetText() == "+" {
		return a + b
	}
	return a - b
}

// errores reemplaza el reporte por defecto de ANTLR (que escribe en stderr).
type errores struct{ *antlr.DefaultErrorListener }

func (e *errores) SyntaxError(_ antlr.Recognizer, _ any, linea, col int, msg string, _ antlr.RecognitionException) {
	fmt.Printf("línea %d:%d: %s\n", linea, col, msg)
}

func main() {
	entrada := antlr.NewIoStream(os.Stdin)
	lexer := parser.NewCalcLexer(entrada)
	p := parser.NewCalcParser(antlr.NewCommonTokenStream(lexer, antlr.TokenDefaultChannel))
	p.RemoveErrorListeners()
	p.AddErrorListener(&errores{antlr.NewDefaultErrorListener()})

	arbol := p.Entrada()
	(&evaluador{vars: map[string]float64{}}).Visit(arbol)
}
