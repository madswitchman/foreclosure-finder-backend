# Use the official Node.js image as the base image
FROM node:18 AS node_base

# Set the working directory inside the container
WORKDIR /app

# Set environment variables
ENV WS_PROTOCOL="wss"
ENV HOST="localhost"
ENV PORT="8080"

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files to the working directory
# COPY . .

# Switch to a Python base image
FROM python:3.8.2-slim AS python_base

# Set the working directory for Python application
WORKDIR /app/scripts

# Copy the Python script and requirements.txt
# COPY api_request.py ./
# COPY requirements.txt ./
COPY app/scripts/api_request.py /app/scripts/
COPY app/scripts/requirements.txt /app/scripts/

# Install necessary build tools including GCC
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Install Python setup tools
RUN apt-get update && apt-get install -y python-setuptools

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Combine Node.js and Python environments
FROM node_base

# Copy the Python script and dependencies from the Python base image
COPY --from=python_base /app/scripts /app/scripts

# Copy the rest of the application files to the working directory
COPY . .

# Expose the port that your app runs on
EXPOSE 8080

# Command to run the application
CMD ["node", "app/index.js"]

# End