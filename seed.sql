INSERT INTO customers (name, email, city, signup_date) VALUES
('Aarav Sharma', 'aarav@example.com', 'Mumbai', '2024-01-15'),
('Priya Nair', 'priya@example.com', 'Bangalore', '2024-02-20'),
('Rohan Mehta', 'rohan@example.com', 'Delhi', '2024-03-10'),
('Sneha Iyer', 'sneha@example.com', 'Chennai', '2024-04-05'),
('Vikram Singh', 'vikram@example.com', 'Pune', '2024-05-12');

INSERT INTO products (name, category, price) VALUES
('Wireless Mouse', 'Electronics', 599.00),
('Mechanical Keyboard', 'Electronics', 2999.00),
('Yoga Mat', 'Fitness', 799.00),
('Running Shoes', 'Fitness', 3499.00),
('Coffee Mug', 'Home', 249.00),
('Desk Lamp', 'Home', 999.00);

INSERT INTO orders (customer_id, order_date, status) VALUES
(1, '2024-06-01', 'completed'),
(2, '2024-06-03', 'completed'),
(1, '2024-06-10', 'completed'),
(3, '2024-06-15', 'pending'),
(4, '2024-06-20', 'completed'),
(5, '2024-06-25', 'completed');

INSERT INTO order_items (order_id, product_id, quantity) VALUES
(1, 1, 2),
(1, 3, 1),
(2, 2, 1),
(3, 5, 3),
(4, 4, 1),
(5, 6, 2),
(6, 1, 1),
(6, 2, 1);