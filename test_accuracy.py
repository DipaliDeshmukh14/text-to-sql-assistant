import os, time, json, urllib.request, urllib.error
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
BASE = "http://127.0.0.1:8000"
engine = create_engine(os.environ["DATABASE_URL"])

# (question, reference SQL that gives the correct answer)
TESTS = [
    ("How many customers are there?",
     "SELECT COUNT(*) FROM customers"),
    ("List all product names with their prices.",
     "SELECT name, price FROM products"),
    ("Show the name and price of the most expensive product.",
     "SELECT name, price FROM products ORDER BY price DESC LIMIT 1"),
    ("How many orders are there?",
     "SELECT COUNT(*) FROM orders"),
    ("What is the average product price?",
     "SELECT AVG(price) FROM products"),
    ("List the distinct product categories.",
     "SELECT DISTINCT category FROM products"),
    ("How many orders have the status completed?",
     "SELECT COUNT(*) FROM orders WHERE status = 'completed'"),
    ("List each order id with the name of the customer who placed it.",
     "SELECT o.id, c.name FROM orders o JOIN customers c ON c.id = o.customer_id"),
    ("How many orders has each customer placed? Show the customer name and the count, and include customers with no orders.",
     "SELECT c.name, COUNT(o.id) FROM customers c LEFT JOIN orders o ON o.customer_id = c.id GROUP BY c.id, c.name"),
    ("List the names of products that have been ordered at least once.",
     "SELECT DISTINCT p.name FROM products p JOIN order_items oi ON oi.product_id = p.id"),
    ("List the names of products that have never been ordered.",
     "SELECT p.name FROM products p LEFT JOIN order_items oi ON oi.product_id = p.id WHERE oi.id IS NULL"),
    ("What is the total quantity sold for each product? Show the product name and total quantity.",
     "SELECT p.name, SUM(oi.quantity) FROM order_items oi JOIN products p ON p.id = oi.product_id GROUP BY p.id, p.name"),
    ("What is the total revenue (price times quantity) across all order items?",
     "SELECT SUM(p.price * oi.quantity) FROM order_items oi JOIN products p ON p.id = oi.product_id"),
    ("What is the total revenue for each product category? Show the category and revenue.",
     "SELECT p.category, SUM(p.price * oi.quantity) FROM order_items oi JOIN products p ON p.id = oi.product_id GROUP BY p.category"),
    ("Show the name and total amount spent for each customer who has placed an order.",
     "SELECT c.name, SUM(p.price * oi.quantity) FROM customers c JOIN orders o ON o.customer_id = c.id JOIN order_items oi ON oi.order_id = o.id JOIN products p ON p.id = oi.product_id GROUP BY c.id, c.name"),
    ("List the cities of customers who have placed at least one order.",
     "SELECT DISTINCT c.city FROM customers c JOIN orders o ON o.customer_id = c.id"),
    ("What is the total quantity of items in order number 1?",
     "SELECT SUM(quantity) FROM order_items WHERE order_id = 1"),
    ("Which product category has the highest total revenue? Show the category and the revenue.",
     "SELECT p.category, SUM(p.price * oi.quantity) AS rev FROM order_items oi JOIN products p ON p.id = oi.product_id GROUP BY p.category ORDER BY rev DESC LIMIT 1"),
    ("Show the ids of orders that contain more than one distinct product.",
     "SELECT order_id FROM order_items GROUP BY order_id HAVING COUNT(DISTINCT product_id) > 1"),
    ("What is the most recent order date?",
     "SELECT MAX(order_date) FROM orders"),
]


def post(path, payload=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def norm(v):
    if v is None:
        return "None"
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return str(v).strip()


def key(rows):
    return sorted(tuple(sorted(norm(v) for v in row)) for row in rows)


def expected(sql):
    with engine.connect() as conn:
        return [list(r) for r in conn.execute(text(sql)).fetchall()]


# warm-up (not counted)
try:
    post("/reset")
    post("/query", {"question": "How many customers are there?"})
except Exception:
    pass

passed, times, report = 0, [], []
for i, (q, ref) in enumerate(TESTS, 1):
    post("/reset")  # clear chat memory so questions don't affect each other
    t0 = time.perf_counter()
    got, err, sql = None, None, None
    try:
        resp = post("/query", {"question": q})
        sql = resp.get("generated_sql")
        got = [list(d.values()) for d in resp.get("results", [])]
    except urllib.error.HTTPError as e:
        err = f"HTTP {e.code}"
    except Exception as e:
        err = str(e)
    dt = time.perf_counter() - t0
    times.append(dt)

    want = expected(ref)
    ok = err is None and key(got) == key(want)
    passed += ok

    print(f"{i:>2}. {'PASS' if ok else 'FAIL'}  {dt:.2f}s  {q}")
    if not ok:
        if err:
            print(f"      error: {err}")
        else:
            print(f"      generated: {sql}")
            print(f"      got:  {got}")
            print(f"      want: {want}")

    report.append({"question": q, "passed": bool(ok), "seconds": round(dt, 2),
                   "generated_sql": sql, "error": err})
    time.sleep(1)  # avoid rate limits

print(f"\nScore: {passed}/{len(TESTS)}  ({passed / len(TESTS) * 100:.0f}%)")
print(f"Average time: {sum(times) / len(times):.2f}s  |  slowest: {max(times):.2f}s")

with open("test_results.json", "w") as f:
    json.dump(report, f, indent=2, default=str)