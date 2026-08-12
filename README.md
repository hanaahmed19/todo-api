# Todo API

A minimal REST API for managing a todo list, built with Python and Flask,
containerized with Docker.

## Project Overview

This project implements a simple CRUD (Create, Read, Update, Delete) REST
API for a todo list. It was built as part of an internship task to practice
the full workflow of developing, containerizing, documenting, and publishing
an application. Todo items are stored in a SQLite database file so data
survives between requests while the app is running.

## Technologies Used

- **Python 3.11**
- **Flask 3.0** — lightweight web framework used to build the REST endpoints
- **SQLite** (via Python's built-in `sqlite3` module) — file-based storage,
  no separate database server required
- **Docker** — containerization

## Project Structure

```
todo-api/
├── app.py              # Flask application (routes + database logic)
├── requirements.txt    # Python dependencies
├── Dockerfile           # Instructions to build the Docker image
├── .dockerignore        # Files excluded from the Docker build context
├── .gitignore            # Files excluded from git
└── README.md            # This file
```

## Prerequisites

- [Python 3.11+](https://www.python.org/downloads/) (only needed to run
  locally without Docker)
- [Docker](https://docs.docker.com/get-docker/) (to build/run the container)
- `curl` or a tool like [Postman](https://www.postman.com/) to test the API

## Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/todo-api.git
   cd todo-api
   ```

## How to Run the Project Locally (without Docker)

1. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. The API is now available at `http://localhost:5000`.

## How to Build the Docker Image

From the project root (where the `Dockerfile` is located):

```bash
docker build -t todo-api .
```

This reads the `Dockerfile`, downloads the base Python image, installs the
dependencies, copies in the application code, and produces a local image
tagged `todo-api`.

## How to Run the Docker Container

```bash
docker run -d -p 5000:5000 --name todo-api-container todo-api
```

- `-d` runs the container in the background (detached mode)
- `-p 5000:5000` maps port 5000 on your machine to port 5000 inside the
  container, where Flask is listening
- `--name` gives the container a memorable name

The API is now available at `http://localhost:5000`.

To view logs: `docker logs todo-api-container`
To stop it: `docker stop todo-api-container`

## API Endpoints

| Method | Endpoint          | Description             |
|--------|-------------------|--------------------------|
| GET    | `/`               | Health check             |
| GET    | `/todos`          | List all todos           |
| GET    | `/todos/<id>`     | Get a single todo        |
| POST   | `/todos`          | Create a todo            |
| PUT    | `/todos/<id>`     | Update a todo            |
| DELETE | `/todos/<id>`     | Delete a todo            |

Example — create a todo:
```bash
curl -X POST http://localhost:5000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Docker"}'
```

## Docker Hub Image

Pushed image: `https://hub.docker.com/r/<your-dockerhub-username>/todo-api`

Pull it directly:
```bash
docker pull <your-dockerhub-username>/todo-api
```

## Screenshots

_(optional — add screenshots of the running app / terminal output here)_
