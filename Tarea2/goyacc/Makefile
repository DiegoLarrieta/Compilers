GOYACC ?= $(HOME)/go/bin/goyacc

calc: calc.go lexer.go
	go build -o calc .

calc.go: calc.y
	$(GOYACC) -p calc -o calc.go calc.y

clean:
	rm -f calc calc.go y.output
