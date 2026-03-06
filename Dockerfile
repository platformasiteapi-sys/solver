# Use Amazon Corretto or GitHub CR to avoid Docker Hub pull limits
FROM public.ecr.aws/docker/library/python:3.10-slim

# Install any required system dependencies for the solver (if it needs shared libraries like libstdc++)
RUN apt-get update && apt-get install -y \
    libstdc++6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the python API code
COPY solver_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY solver_api/main.py .
COPY solver_api/solver_config.py .

# IMPORTANT: The linux release of the solver!
# The user MUST put the Linux `console_solver` binary AND the `resources` folder into
# the `linux_bin` folder before building the image on their remote server.
COPY linux_bin/console_solver /app/console_solver
COPY linux_bin/resources /app/resources
RUN chmod +x /app/console_solver

# Tell the Python app where to find the solver
ENV SOLVER_PATH="/app/console_solver"

# Expose the port Uvicorn will run on
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
