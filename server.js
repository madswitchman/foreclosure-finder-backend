const express = require('express');
const { spawn } = require('child_process');
const bodyParser = require('body-parser');
const app = express();
const port = 3000;

// Parse JSON request
app.use(bodyParser.json());

app.get('/run-script', (req, res) => {
    // Extract data from the request query params
    const requestData = req.query;

    // Execute Python script as a child process
    const pythonProcess = spawn('python', ['scripts/api_request.py']);

    // Send POST data to Python script's stdin
    pythonProcess.stdin.write(JSON.stringify(requestData));
    pythonProcess.stdin.end();

    // Capture error messages
    let output = '';
    let errorOutput = '';
    let requestCancelled = false; // Flag to track request cancellation

    // Event handler for request cancellation for GET request
    req.on('close', () => {
        // If the request is canceled, set the flag and terminate the Python process
        requestCancelled = true;
        pythonProcess.kill('SIGTERM');
    });

    pythonProcess.stdout.on('data', (data) => {
        if (!requestCancelled) {
            output += data;
            // Log the stdout data for debugging
            console.log(`${data}`);
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        if (!requestCancelled) {
            errorOutput += data;
            // Log the stderr data for debugging
            console.error(`ERROR: ${data}`);
        }
    });

    pythonProcess.on('close', (code) => {
        if (code === 0 && !requestCancelled) {
            // Return the output as the HTTP response
            res.status(200).json({ result: 'Request complete.' });
        } else if (requestCancelled) {
            // Handle cancellation by sending a response
            res.status(400).json({ error: 'Request was canceled.' });
        } else {
            // Handle script execution error
            res.status(500).json({ error: 'Script execution error.' });
            // Log the errorOutput for debugging
            console.error(`Python script execution error:\n${errorOutput}`);
        }
    });
});

// Handle other routes
app.use((req, res) => {
    res.status(404).send('Not Found');
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});
