const admin = require("firebase-admin");
const express = require("express");
const fs = require('fs');
const path = require('path');
const { spawn } = require("child_process");
const { Storage } = require('@google-cloud/storage');

admin.initializeApp({});

const app = express();
const host = process.env.HOST || 'localhost';
const port = process.env.PORT || 8080; // Set default port to 8080

// Initialize Google Cloud Storage client
const storage = new Storage();

let pythonProcess;
let progressData = {progress: 0};
let fileInfoData = {filename: '', fileUrl: ''};

app.set("view engine", "ejs");
app.set("views", "app/views");

process.env.PYTHONUNBUFFERED = 'true';

// Render the HTML template when /run-script is accessed
app.get("/run-script", (req, res) => {
    // Start the Python script if it hasn't been started yet
    if (!pythonProcess) {
        console.log("process.env.HOST value: ", process.env.HOST);

        if (process.env.HOST === 'foreclosure-finder-backend-lv672goida-uc.a.run.app') {
            pythonProcess = spawn('./scripts/dist/api_request');
        } else {
            pythonProcess = spawn('python', ['./app/scripts/api_request.py']);
        }
        
        pythonProcess.stdin.write(JSON.stringify(req.query));
        pythonProcess.stdin.end();

        // Listen for data from the Python process and update progressData accordingly
        pythonProcess.stdout.on("data", (data) => {
            const lines = data.toString().split("\n");
            lines.forEach((line) => {
                try {
                    const progressMatch = line.match(/{"progress":([^}]*)}/);
                    if (progressMatch && progressMatch[1] !== null) {
                        progressData = { progress: progressMatch[1] };
                    }
                    const fileInfoMatch = line.match(/{"\s*type\s*":\s*"fileInfo"\s*,\s*"fileName"\s*:\s*"([^"]*)"\s*,\s*"fileUrl"\s*:\s*"([^"]*)"\s*}/);
                    if (fileInfoMatch && fileInfoMatch[1] !== null) {
                        const filename = fileInfoMatch[1];
                        const fileUrl = fileInfoMatch[2];
                        fileInfoData = { filename, fileUrl };
                    }
                } catch (error) {
                    console.error("Error parsing data:", error);
                }
            });
        });

        // Handle errors from the Python process
        pythonProcess.stderr.on("data", (data) => {
            console.error(`ERROR: ${data.toString()}`);
        });

        // Handle the Python process exit
        pythonProcess.on("exit", (code) => {
            console.log(`Python script exited with code ${code}`);
            // Reset progressData and pythonProcess variables
            pythonProcess = null;
        });
    }
    res.render("progress");
});

// Endpoint to fetch progress updates
app.get("/progress-updates", (req, res) => {
    // Send the current progress data
    res.json(progressData);
});

app.get("/file-link", (req, res) => {
    if (fileInfoData) {
        res.json({ fileInfo: fileInfoData });
    }
});

app.get("/download-csv", async (req, res) => {
    if (fileInfoData) {
        try {
            // Set up options for downloading the file
            const options = {
                destination: fileInfoData.filename
            };

            // Download the file from Google Cloud Storage to local
            await storage.bucket('foreclosurefinderbackend').file(fileInfoData.filename).download(options);

            // Construct the absolute path to the downloaded file
            const absolutePath = path.resolve(__dirname, '..', fileInfoData.filename);

            // Set the Content-Disposition header
            res.setHeader('Content-Disposition', `attachment; filename="${fileInfoData.filename}"`);

            // Stream the file to the response
            const fileStream = fs.createReadStream(absolutePath);
            fileStream.pipe(res);

            // When the stream ends, delete the file
            fileStream.on('end', () => {
                fs.unlink(absolutePath, (unlinkErr) => {
                    if (unlinkErr) {
                        console.error("Error deleting file:", unlinkErr);
                    } else {
                        console.log("File deleted successfully");
                    }
                });
            });

            // Return to avoid sending the response again
            return;
        } catch (error) {
            console.error("Error downloading file:", error);
            return res.status(500).send("Internal Server Error");
        }
    } else {
        return res.status(404).send("File not found");
    }
});


app.use((req, res) => {
    return res.status(404).send("Not Found");
});

const server = app.listen(port, () => {
    console.log(`HTTP Server is listening on ${host}:${port}`);
});

module.exports = server; // Export server for testing
