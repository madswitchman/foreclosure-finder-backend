# First stage: Install Node.js dependencies
FROM node:18 AS node_build

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Second stage: Install Python and dependencies
FROM python:3.8.2-slim AS python_build

# Install PyInstaller
RUN pip install pyinstaller

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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Third stage: Package Python application using PyInstaller
RUN pyinstaller --onefile /app/scripts/api_request.py

# Final stage
FROM node_build AS final

# Set the working directory inside the container
WORKDIR /app

# Copy the packaged Python executable into the final image
COPY --from=python_build /app/scripts/dist/api_request /app/scripts/dist/api_request

# Copy the Node.js application files
COPY app/ app/

# Set environment variables
ENV WS_PROTOCOL="wss://"
ENV HOST="foreclosure-finder-backend-lv672goida-uc.a.run.app"
ENV PYTHONUNBUFFERED = 'true';

# Command to run the application
CMD ["node", "app/index.js"]