calc: calc.tab.c lex.yy.c
	cc -o calc calc.tab.c lex.yy.c -lm

calc.tab.c calc.tab.h: calc.y
	bison -d calc.y

lex.yy.c: calc.l calc.tab.h
	flex calc.l

clean:
	rm -f calc calc.tab.c calc.tab.h lex.yy.c calc.output
