"""
Todo REST API
A tiny CRUD (Create, Read, Update, Delete) application built with Flask.

Data is stored in a local SQLite database file (todos.db), which is
created automatically the first time the app runs.
"""

from flask import Flask, jsonify, request, abort
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
