# Use the official Node.js image as the base image
FROM node:18

# Set the working directory inside the container
WORKDIR /app

# Set environment variables
ENV wsProtocol="wss"
ENV host="localhost"
ENV port="8080"

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files to the working directory
COPY . .

# Expose the port that your app runs on
EXPOSE 8080

# Command to run the application
CMD ["node", "app/index.js"]

# End