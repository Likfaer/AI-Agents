class Calculator {
    constructor(previousOperandElement, currentOperandElement) {
        this.previousOperandElement = previousOperandElement;
        this.currentOperandElement = currentOperandElement;
        this.clear();
    }

    clear() {
        this.currentOperand = '';
        this.previousOperand = '';
        this.operation = undefined;
        this.resetDisplay();
    }

    delete() {
        this.currentOperand = this.currentOperand.toString().slice(0, -1);
    }

    appendNumber(number) {
        if (number === '.' && this.currentOperand.includes('.')) return;
        this.currentOperand = this.currentOperand.toString() + number.toString();
    }

    chooseOperation(operation) {
        if (this.currentOperand === '') return;
        if (this.previousOperand !== '') {
            this.compute();
        }
        this.operation = operation;
        this.previousOperand = this.currentOperand;
        this.currentOperand = '';
    }

    compute() {
        let computation;
        const prev = parseFloat(this.previousOperand);
        const current = parseFloat(this.currentOperand);
        
        if (isNaN(prev) || isNaN(current)) return;
        
        switch (this.operation) {
            case '+':
                computation = prev + current;
                break;
            case '-':
                computation = prev - current;
                break;
            case '*':
                computation = prev * current;
                break;
            case '/':
                if (current === 0) {
                    alert('Деление на ноль невозможно!');
                    this.clear();
                    return;
                }
                computation = prev / current;
                break;
            default:
                return;
        }
        
        // Округляем до разумного количества знаков после запятой
        const precision = 10000000000;
        computation = Math.round(computation * precision) / precision;
        
        this.currentOperand = computation;
        this.operation = undefined;
        this.previousOperand = '';
    }

    getDisplayNumber(number) {
        const stringNumber = number.toString();
        const integerDigits = parseFloat(stringNumber.split('.')[0]);
        const decimalDigits = stringNumber.split('.')[1];
        
        let integerDisplay;
        if (isNaN(integerDigits)) {
            integerDisplay = '';
        } else {
            integerDisplay = integerDigits.toLocaleString('ru', { maximumFractionDigits: 0 });
        }
        
        if (decimalDigits != null) {
            return `${integerDisplay}.${decimalDigits}`;
        } else {
            return integerDisplay;
        }
    }

    resetDisplay() {
        this.currentOperandElement.innerText = '0';
        this.previousOperandElement.innerText = '';
    }

    updateDisplay() {
        this.currentOperandElement.innerText = 
            this.getDisplayNumber(this.currentOperand);
        
        if (this.operation != null) {
            const symbolMap = {
                '+': '+',
                '-': '-',
                '*': '×',
                '/': '÷'
            };
            this.previousOperandElement.innerText = 
                `${this.getDisplayNumber(this.previousOperand)} ${symbolMap[this.operation]}`;
        } else {
            this.previousOperandElement.innerText = '';
        }
    }
}

// Получаем элементы из DOM
const previousOperandElement = document.getElementById('previous-operand');
const currentOperandElement = document.getElementById('current-operand');

// Создаем калькулятор
const calculator = new Calculator(previousOperandElement, currentOperandElement);

// Добавляем обработчики событий для кнопок
document.querySelectorAll('.buttons button').forEach(button => {
    button.addEventListener('click', () => {
        const number = button.dataset.number;
        const operation = button.dataset.operation;
        const action = button.dataset.action;

        if (number) {
            calculator.appendNumber(number);
            calculator.updateDisplay();
        } else if (operation) {
            calculator.chooseOperation(operation);
            calculator.updateDisplay();
        } else if (action === 'clear') {
            calculator.clear();
            calculator.resetDisplay();
        } else if (action === 'delete') {
            calculator.delete();
            calculator.updateDisplay();
        } else if (action === 'equals') {
            calculator.compute();
            calculator.updateDisplay();
        }
    });
});
