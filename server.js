const express = require('express');
const { spawn } = require('child_process');
const http = require('http');
const WebSocket = require('ws');
const app = express();
const port = 3000;
const server = http.createServer(app);


// Use EJS as the templating engine
app.set('view engine', 'ejs');

// Function to send progress updates to connected clients
function sendProgressUpdate(progress) {
    console.log(progress)
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ progress }));
        }
    });
}

// Init WSS for client/progress updates (port 3000)
const wss = new WebSocket.Server({ server });

// WebSocket connection handling
wss.on('connection', (ws) => {
    // Handle WebSocket connections for sending progress updates
    console.log('WebSocket client connected');

    // Optionally, you can send an initial message to the client
    ws.send(JSON.stringify({ type: 'connected', message: 'WebSocket connection established.' }));

    ws.on('close', () => {
        console.log('WebSocket client disconnected');
    });
});

app.get('/run-script', (req, res) => {
    // Extract data from the request query params
    const requestData = req.query;

    // Render the 'progress.ejs' template
    res.render('progress');

    // Init WSS for Python script (port 4000)
    const scriptSocket = new WebSocket('ws://localhost:4000', { perMessageDeflate: false });

    scriptSocket.addEventListener('open', function (event) {
        // Send a message to start the script
        scriptSocket.send(JSON.stringify({ startScript: true }));
    });

    scriptSocket.addEventListener('close', () => {
        console.log('WebSocket scriptSocket disconnected');
    });

    // Event handler for messages from the scriptSocket
    scriptSocket.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);
        console.log("Received message from scriptSocket:", data);

        if (data.type === 'complete') {
            // Handle script completion
            res.status(200).json({ result: 'Request complete.' });
        } else {
            // Handle other message types if needed
        }
    });

    // Start the Python script as a child process
    const pythonProcess = spawn('python', ['scripts/api_request.py']);

    // Send POST data to Python script's stdin
    pythonProcess.stdin.write(JSON.stringify(requestData));
    pythonProcess.stdin.end();

    // Handle script output and update progress
    pythonProcess.stdout.on('data', (data) => {
        const lines = data.toString().split('\n');
        lines.forEach((line) => {
            try {
                const progressMatch = line.match(/{"progress":([^}]*)}/);
                if (progressMatch && progressMatch[1] !== null) {
                    const progressData = JSON.parse(progressMatch[0]);
                    sendProgressUpdate(progressData.progress);
                }
            } catch (error) {
                console.error('Error parsing progress data:', error);
            }
        });
    });

    // Handle script errors
    pythonProcess.stderr.on('data', (data) => {
        console.error(`ERROR: ${data.toString()}`);
    });

    pythonProcess.on('close', (code) => {
        console.log('Python script closed with code', code);
        // Notify the scriptSocket about script completion
        scriptSocket.send(JSON.stringify({ type: 'complete' }));
        // Close the scriptSocket
        scriptSocket.close();
    });
});

// Handle other routes
app.use((req, res) => {
    res.status(404).send('Not Found');
});

// // Start the server
server.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});