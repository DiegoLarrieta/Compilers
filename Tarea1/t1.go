package main

// repo : https://github.com/DiegoLarrieta/Compilers

import "fmt"

// Tarea 1: Implementar una pila (Stack) y una cola (Queue) en Go.

// =====================================================
// PILA (Stack) - LIFO: el último que entra es el primero que sale
// =====================================================

// Stack guarda sus elementos en un slice (lista de Go)
type Stack struct {
	items []int
}

// IsEmpty regresa true si la pila no tiene elementos
func (s *Stack) IsEmpty() bool { return len(s.items) == 0 }

// Push agrega un elemento al final (arriba de la pila)
func (s *Stack) Push(item int) { s.items = append(s.items, item) }

// Pop saca y regresa el último elemento (el de arriba)
func (s *Stack) Pop() int {
	item := s.items[len(s.items)-1]    // tomo el último
	s.items = s.items[:len(s.items)-1] // lo quito de la lista
	return item
}

// Peek regresa el último elemento sin sacarlo
func (s *Stack) Peek() int { return s.items[len(s.items)-1] }

// Size regresa cuántos elementos tiene la pila
func (s *Stack) Size() int { return len(s.items) }

// =====================================================
// COLA (Queue) - FIFO: el primero que entra es el primero que sale
// =====================================================

// Queue guarda sus elementos en un slice (lista de Go)
type Queue struct {
	items []int
}

// IsEmpty regresa true si la cola no tiene elementos
func (q *Queue) IsEmpty() bool { return len(q.items) == 0 }

// Enqueue agrega un elemento al final de la cola
func (q *Queue) Enqueue(item int) { q.items = append(q.items, item) }

// Dequeue saca y regresa el primer elemento de la cola
func (q *Queue) Dequeue() int {
	item := q.items[0]    // tomo el primero
	q.items = q.items[1:] // lo quito de la lista
	return item
}

// Size regresa cuántos elementos tiene la cola
func (q *Queue) Size() int { return len(q.items) }

// =====================================================
// TEST CASES
// =====================================================
func main() {
	fmt.Println("===== PILA =====")

	// Test case 1: una pila nueva está vacía
	stack := &Stack{}
	fmt.Println("Test 1 - ¿Pila vacía?:", stack.IsEmpty()) // true

	// Test case 2: push de 1, 2, 3 -> tamaño 3
	stack.Push(1)
	stack.Push(2)
	stack.Push(3)
	fmt.Println("Test 2 - Tamaño después de push:", stack.Size()) // 3

	// Test case 3: peek regresa el último sin sacarlo
	fmt.Println("Test 3 - Peek:", stack.Peek()) // 3

	// Test case 4: pop saca el último que entró
	fmt.Println("Test 4 - Pop:", stack.Pop()) // 3

	// Test case 5: después del pop, el de arriba es 2
	fmt.Println("Test 5 - Peek después de pop:", stack.Peek()) // 2

	// Test case 6: tamaño después del pop
	fmt.Println("Test 6 - Tamaño:", stack.Size()) // 2

	// Test case 7: ya no está vacía
	fmt.Println("Test 7 - ¿Pila vacía?:", stack.IsEmpty()) // false

	fmt.Println("\n===== COLA =====")

	// Test case 8: una cola nueva está vacía
	queue := &Queue{}
	fmt.Println("Test 8 - ¿Cola vacía?:", queue.IsEmpty()) // true

	// Test case 9: enqueue de 1, 2, 3 -> tamaño 3
	queue.Enqueue(1)
	queue.Enqueue(2)
	queue.Enqueue(3)
	fmt.Println("Test 9 - Tamaño después de enqueue:", queue.Size()) // 3

	// Test case 10: dequeue saca el primero que entró
	fmt.Println("Test 10 - Dequeue:", queue.Dequeue()) // 1

	// Test case 11: el siguiente dequeue saca el 2
	fmt.Println("Test 11 - Dequeue:", queue.Dequeue()) // 2

	// Test case 12: tamaño después de dos dequeue
	fmt.Println("Test 12 - Tamaño:", queue.Size()) // 1

	// Test case 13: ya no está vacía
	fmt.Println("Test 13 - ¿Cola vacía?:", queue.IsEmpty()) // false
}

// Uso de IA : Claude (Gratis):
// Se utilizo claude para aclrar dudas de sintaxis y funcionamiento de Go, asi como para sugerencias de implementacion de la pila y cola.
