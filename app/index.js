//const functions = require("firebase-functions");
const WebSocket = require("ws");
const express = require("express");
const {spawn} = require("child_process");
const admin = require("firebase-admin");

admin.initializeApp({});

const app = express();
const host = process.env.HOST || 'localhost';
const port = process.env.PORT || 8080;
app.set("view engine", "ejs");
app.set("views", "app/views");

// Set the environment variable PYTHONUNBUFFERED to true
process.env.PYTHONUNBUFFERED = 'true';

const httpServer = app.listen(port, () => {
  const wsProtocol = process.env.WS_PROTOCOL || 'ws://';
  console.log(`HTTP Server is listening on ${host}:${port}`);

  const fileInfo = {}; // Object to store fileInfo data

  const wss = new WebSocket.Server({server: httpServer});

  wss.on("connection", (ws) => {
    console.log("WebSocket index.js connected");

    // Send fileInfo message when WebSocket connection is established
    if (fileInfo.fileName && fileInfo.fileUrl) {
      ws.send(JSON.stringify({
        type: "fileInfo",
        fileName: fileInfo.fileName,
        fileUrl: fileInfo.fileUrl,
      }));
    }

    // ws.on("message", (message) => {
    //   console.log("Received message from client:", message.toString());
    // });
    ws.onmessage = function(event) {
      console.log("Received message from client:", event.data);
      // You can access the received message using event.data
    };

    // ws.on("close", () => {
    //   console.log("WebSocket index.js disconnected");
    // });
    ws.onclose = function() {
      console.log("WebSocket index.js disconnected");
    };
  });

  app.get("/run-script", (req, res) => {
    const requestData = req.query;
    console.log("Request data: ", requestData);
    console.log("WS_PROTOCOL: ", wsProtocol);
    console.log("HOST: ", host);
    const pythonProcess = spawn("python", ["app/scripts/api_request.py", wsProtocol, host, port]);

    pythonProcess.stdin.write(JSON.stringify(requestData));
    pythonProcess.stdin.end();

    res.render("progress", {wsProtocol, host, port});

    // eslint-disable-next-line require-jsdoc
    function sendProgressUpdate(progress) {
      // console.log(progress);
      wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify({progress}));
        }
      });
    }

    pythonProcess.stdout.on("data", (data) => {
      const message = data.toString();
      console.log("Received message from Python script:", message);

      const lines = data.toString().split("\n");
      lines.forEach((line) => {
        try {
          const progressMatch = line.match(/{"progress":([^}]*)}/);

          if (progressMatch && progressMatch[1] !== null) {
            const progressData = JSON.parse(progressMatch[0]);
            sendProgressUpdate(progressData.progress);
            // console.log("progressMatch: ", progressMatch[1]);
          }
          // if (progressData.progress === 100) {
          // console.log("Made it to line 89");
          // const fileInfoMatch = line.match(/{"type":([^}]*)}/);

          // eslint-disable-next-line max-len
          // const fileInfoMatch = line.match(/{"type": "fileInfo", "fileName": "([^"]*)", "fileUrl": "([^"]*)"/);
          // eslint-disable-next-line max-len
          const fileInfoMatch = line.match(/{"\s*type\s*":\s*"fileInfo"\s*,\s*"fileName"\s*:\s*"([^"]*)"\s*,\s*"fileUrl"\s*:\s*"([^"]*)"\s*}/);
          // console.log("At fileInfoMatch");
          // console.log(fileInfoMatch);
          // console.log("fileInfoMatch: ", fileInfoMatch);
          // console.log("Received fileInfo:", fileInfo);

          if (fileInfoMatch) {
            console.log("fileInfoMatch is not null");
          }
          // const fileNameData = JSON.parse(fileInfoMatch[0]);
          // const fileName = fileNameData.fileName;
          // const fileUrl = fileNameData.fileUrl;
          // const fileInfoData = JSON.parse(fileNameData[0]);
          // console.log("fileInfoMatch: ", fileInfoMatch);
          // console.log("fileNameData: ", fileNameData);
          // console.log("fileName: ", fileName);
          // console.log("fileUrl: ", fileUrl);
          // console.log("fileInfoData: ", fileInfoData);
          // Emit a WebSocket message with file information
          if (fileInfoMatch && fileInfoMatch[1] !== null) {
            console.log("Inside fileInfoMatch");
            // const fileName = fileInfoMatch[1];
            // const fileUrl = fileInfoMatch[2];
            const fileName = fileInfoMatch[1];
            const fileUrl = fileInfoMatch[2];
            // console.log("Received fileInfo:", fileInfo);
            console.log("Received fileInfo:", {fileName, fileUrl});

            // Debugging log statement to confirm the fileInfo message sending
            console.log("Sending fileInfo message:", fileInfo);

            wss.clients.forEach((client) => {
              if (client.readyState === WebSocket.OPEN) {
                // console.log("We are in the web socket emit - line 93");
                client.send(JSON.stringify({
                  type: "fileInfo",
                  fileName: fileName,
                  fileUrl: fileUrl,
                }));
              }
            });
            // }
          }
        } catch (error) {
          console.error("Error parsing progress data:", error);
        }
      });
    });

    pythonProcess.stderr.on("data", (data) => {
      console.error(`ERROR: ${data.toString()}`);
    });

    pythonProcess.on("close", (code) => {
      console.log("Python script closed with code", code);
    });
  });

  app.use((req, res) => {
    return res.status(404).send("Not Found");
  });
});

//exports.app = functions.https.onRequest(app);
module.exports = app;
