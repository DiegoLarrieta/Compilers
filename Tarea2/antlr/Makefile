ANTLR_JAR ?= antlr-4.13.2-complete.jar

calc: parser/calc_parser.go main.go
	go build -o calc .

parser/calc_parser.go: Calc.g4
	java -jar $(ANTLR_JAR) -Dlanguage=Go -visitor -no-listener -package parser -o parser Calc.g4

clean:
	rm -rf calc parser
