# Set environment variables
ENV WS_PROTOCOL="wss"
ENV HOST="localhost"
ENV PORT="8080"


# Use an official Node.js runtime as the base image
FROM node:18-slim AS node_base

# Set the working directory for Node.js application
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Switch to a Python base image
FROM python:3.8.2-slim AS python_base

# Set the working directory for Python application
WORKDIR /app

# Copy the Python script and requirements.txt
COPY api_request.py ./
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Combine Node.js and Python environments
FROM node_base

# Copy the Python script and dependencies from the Python base image
COPY --from=python_base /app .

# Expose the port(s) your app listens on
EXPOSE $PORT

# Command to run your application
CMD ["node", "index.js"]