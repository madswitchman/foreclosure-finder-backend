# First stage: Install Python dependencies in a venv
FROM python:3.8.2-slim AS python_build

# Set the working directory for Python application
WORKDIR /app/scripts

# Copy the Python script and requirements.txt
COPY app/scripts/api_request.py /app/scripts/
COPY app/scripts/requirements.txt /app/scripts/

# Install necessary build tools including GCC
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/app/venv
ENV PATH="/opt/app/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Second stage: Build Node.js application
FROM node:18 AS node_build

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Third stage: Combine Node.js and Python environments
FROM node_build AS final

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script and dependencies from the Python build stage
COPY --from=python_build /opt/app/venv /opt/app/venv

# Copy the rest of the application files to the working directory
COPY . .

# Set environment variables
ENV WS_PROTOCOL="wss://"
ENV HOST="foreclosure-finder-backend-lv672goida-uc.a.run.app"

# Command to run the application
CMD ["node", "app/index.js"]