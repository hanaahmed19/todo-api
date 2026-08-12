"""
Todo REST API
A tiny CRUD (Create, Read, Update, Delete) application built with Flask.

Data is stored in a local SQLite database file (todos.db), which is
created automatically the first time the app runs.
"""

from flask import Flask, jsonify, request, abort, render_template_string
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "todos.db")


def get_db_connection():
    """Open a connection to the SQLite database.

    row_factory = sqlite3.Row lets us access columns by name
    (e.g. row["title"]) instead of only by index (row[0]).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the todos table if it doesn't exist yet.

    This runs once when the app starts, so the container/app is
    ready to use immediately without a separate setup step.
    """
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def todo_to_dict(row):
    """Convert a sqlite3.Row into a plain dict that Flask can turn into JSON."""
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.route("/", methods=["GET"])
def health_check():
    """Simple endpoint to confirm the API is running."""
    return jsonify({"status": "ok", "message": "Todo API is running"})


UI_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Todo API</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 480px; margin: 40px auto; padding: 0 16px; background: #f7f7f9; }
        h1 { font-size: 22px; }
        form { display: flex; gap: 8px; margin-bottom: 20px; }
        input[type=text] { flex: 1; padding: 8px 10px; border: 1px solid #ccc; border-radius: 6px; }
        button { padding: 8px 14px; border: none; border-radius: 6px; background: #2563eb; color: white; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        ul { list-style: none; padding: 0; }
        li { display: flex; align-items: center; gap: 10px; background: white; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
        li.done span.title { text-decoration: line-through; color: #999; }
        .del { margin-left: auto; background: #dc2626; }
        .del:hover { background: #b91c1c; }
    </style>
</head>
<body>
    <h1>My Todos</h1>
    <form id="add-form">
        <input type="text" id="title-input" placeholder="Add a new todo..." required>
        <button type="submit">Add</button>
    </form>
    <ul id="todo-list"></ul>

    <script>
        async function loadTodos() {
            const res = await fetch('/todos');
            const todos = await res.json();
            const list = document.getElementById('todo-list');
            list.innerHTML = '';
            todos.forEach(todo => {
                const li = document.createElement('li');
                if (todo.done) li.classList.add('done');
                li.innerHTML = `
                    <input type="checkbox" ${todo.done ? 'checked' : ''} data-id="${todo.id}" class="toggle">
                    <span class="title">${todo.title}</span>
                    <button class="del" data-id="${todo.id}">Delete</button>
                `;
                list.appendChild(li);
            });
        }

        document.getElementById('add-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('title-input');
            await fetch('/todos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: input.value})
            });
            input.value = '';
            loadTodos();
        });

        document.getElementById('todo-list').addEventListener('click', async (e) => {
            if (e.target.classList.contains('del')) {
                await fetch('/todos/' + e.target.dataset.id, {method: 'DELETE'});
                loadTodos();
            }
        });

        document.getElementById('todo-list').addEventListener('change', async (e) => {
            if (e.target.classList.contains('toggle')) {
                await fetch('/todos/' + e.target.dataset.id, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({done: e.target.checked})
                });
                loadTodos();
            }
        });

        loadTodos();
    </script>
</body>
</html>
"""


@app.route("/ui", methods=["GET"])
def ui_page():
    """A simple human-viewable webpage for the todo list.

    This is optional -- the app is really an API. This page just calls
    the same /todos endpoints in the background using JavaScript
    (fetch), so you have something to click and see instead of raw JSON.
    """
    return render_template_string(UI_PAGE)


@app.route("/todos", methods=["GET"])
def get_todos():
    """Return every todo item."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()
    return jsonify([todo_to_dict(row) for row in rows])


@app.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    """Return a single todo item by id, or 404 if it doesn't exist."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    if row is None:
        abort(404, description="Todo not found")
    return jsonify(todo_to_dict(row))


@app.route("/todos", methods=["POST"])
def create_todo():
    """Create a new todo item.

    Expects JSON body: {"title": "Buy milk"}
    """
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if not title:
        abort(400, description="'title' is required")

    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO todos (title, done) VALUES (?, 0)", (title,)
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(todo_to_dict(row)), 201


@app.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    """Update an existing todo's title and/or done status.

    Expects JSON body with any of: {"title": "...", "done": true}
    """
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        conn.close()
        abort(404, description="Todo not found")

    data = request.get_json(silent=True) or {}
    new_title = data.get("title", row["title"])
    new_done = data.get("done", bool(row["done"]))

    conn.execute(
        "UPDATE todos SET title = ?, done = ? WHERE id = ?",
        (new_title, int(bool(new_done)), todo_id),
    )
    conn.commit()
    updated_row = conn.execute(
        "SELECT * FROM todos WHERE id = ?", (todo_id,)
    ).fetchone()
    conn.close()
    return jsonify(todo_to_dict(updated_row))


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    """Delete a todo item by id."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        conn.close()
        abort(404, description="Todo not found")

    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Todo {todo_id} deleted"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e.description)}), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e.description)}), 400


if __name__ == "__main__":
    init_db()
    # host="0.0.0.0" is required so the server accepts connections
    # from outside the container, not just from localhost inside it.
    app.run(host="0.0.0.0", port=5000, debug=False)
