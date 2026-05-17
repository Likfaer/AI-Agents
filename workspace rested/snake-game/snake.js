const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = 400;
canvas.height = 400;

// Game variables and constants
let snake = [{ x: 200, y: 200 }];
let food = { x: 300, y: 300 };
let dx = 10;
let dy = 0;

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Draw snake
    snake.forEach(segment => {
        ctx.fillStyle = 'green';
        ctx.fillRect(segment.x, segment.y, 10, 10);
    });
    // Draw food
    ctx.fillStyle = 'red';
    ctx.fillRect(food.x, food.y, 10, 10);
}

function update() {
    const head = { x: snake[0].x + dx, y: snake[0].y + dy };
    snake.unshift(head);
    if (head.x === food.x && head.y === food.y) {
        // Food eaten, generate new food
        food = { x: Math.floor(Math.random() * 40) * 10, y: Math.floor(Math.random() * 40) * 10 };
    } else {
        snake.pop();
    }
}

function gameLoop() {
    update();
    draw();
    setTimeout(gameLoop, 100);
}
gameLoop();