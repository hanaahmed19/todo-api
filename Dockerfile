# 1. Base image: a small, official Python 3.11 image.
#    "slim" leaves out compilers/docs we don't need, so the final
#    image is smaller and has a smaller attack surface.
FROM python:3.11-slim

# 2. Set the working directory inside the container.
#    Every instruction after this (COPY, RUN, CMD) runs relative to /app.
WORKDIR /app

# 3. Copy ONLY the dependency file first, not the whole project.
#    Docker caches each instruction as a "layer". As long as
#    requirements.txt doesn't change, Docker reuses the cached
#    "pip install" layer on rebuilds instead of redownloading
#    everything -- this is why we copy code separately, later.
COPY requirements.txt .

# 4. Install dependencies.
#    --no-cache-dir stops pip from keeping its download cache,
#    which would otherwise bloat the image for no benefit
#    (we never reuse that cache inside the container).
RUN pip install --no-cache-dir -r requirements.txt

# 5. Now copy the rest of the application code.
#    This layer changes often (every code edit), so it's placed
#    AFTER the slow "pip install" layer on purpose.
COPY . .

# 6. Document which port the app listens on.
#    EXPOSE doesn't actually publish the port -- it's metadata/
#    documentation. The real publishing happens with `-p` on `docker run`.
EXPOSE 5000

# 7. Default command executed when a container starts from this image.
#    Exec form (JSON array) is preferred over the shell form because
#    it runs the process directly as PID 1, so it receives signals
#    like SIGTERM correctly (e.g. for `docker stop`).
CMD ["python", "app.py"]
