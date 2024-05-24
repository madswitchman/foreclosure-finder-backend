const axios = require('axios');
const express = require("express");
const cors = require('cors');
const bodyParser = require('body-parser')
const { Storage } = require('@google-cloud/storage');

const app = express();
const storage = new Storage();

let progressData = { progress: 0 };
let fileInfoData = { filename: '', fileUrl: '' };

// Enable CORS for all routes
app.use(cors());

app.use(bodyParser.json())

app.set("view engine", "ejs");
app.set("views", "app/views");

// Function to log and transform query parameters
const transformQueryToJSON = (query) => {
    const jsonObject = {};
    for (const [key, value] of Object.entries(query)) {
        jsonObject[key] = value;
    }
    return jsonObject;
};


// app.get("/run-script", async (req, res) => {
//     try {
//         res.render("progress");
//         console.log('req.query: ', req.query);
//         await callPythonFunction(req.query);
//     } catch (error) {
//         //console.error("Error calling Python function:", error);
//         res.status(500).send("Internal Server Error");
//     }
// });

app.get("/run-script", async (req, res) => {
    try {
        console.log('Received request at /run-script with query:', req.query);
        res.render("progress");
        const transformedQuery = transformQueryToJSON(req.query);
        console.log('Transformed query to JSON:', transformedQuery);
        await callPythonFunction(transformedQuery);
    } catch (error) {
        console.error("Error calling Python function:", error.message);
        res.status(500).send("Internal Server Error");
    }
});

app.get("/progress-updates", (req, res) => {
    res.json(progressData);
});

app.post('/progress-updates', (req, res) => {
    try {
        //const progress = req.body.progress;
        progressData.progress = req.body.progress;
        console.log('Received progress update:', progressData.progress);
        //res.json({ progress });
        res.json({ progress: progressData.progress });
    } catch (error) {
        console.error('Error handling progress update:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.get("/file-link", (req, res) => {
    if (fileInfoData) {
        res.json({ fileInfo: fileInfoData });
    } else {
        res.status(404).send("File not found");
    }
});

app.post('/file-link', (req, res) => {
    const fileInfo = req.body;
    console.log('Received file information:', fileInfo);

    if (fileInfoData) {
        res.json({ fileInfo: fileInfoData });
    } else {
        res.status(404).send("File not found");
    }
});

app.get("/download-csv", async (req, res) => {
    if (fileInfoData) {
        try {
            const options = {
                destination: fileInfoData.filename
            };

            await storage.bucket('foreclosurefinderbackend').file(fileInfoData.filename).download(options);

            res.setHeader('Content-Disposition', `attachment; filename="${fileInfoData.filename}"`);

            const fileStream = storage.bucket('foreclosurefinderbackend').file(fileInfoData.filename).createReadStream();
            fileStream.pipe(res);

            return;
        } catch (error) {
            console.error("Error downloading file:", error);
            res.status(500).send("Internal Server Error");
        }
    } else {
        res.status(404).send("File not found");
    }
});

// app.get('/test-connection', async (req, res) => {
//     try {
//         const response = await axios.get(
//             'https://us-central1-foreclosurefinderbackend.cloudfunctions.net/fetch_data',
//             req.query.state,
//             { headers: { 'Content-Type': 'application/json' } }
//           );
//           res.send(response.data);
//     } catch (error) {
//       console.error('Error connecting to Cloud Function:', error.response ? error.response.data : error.message);
//       res.status(500).send('Error connecting to Cloud Function');
//     }
// });

app.post('/test-connection', async (req, res) => {
    try {
        const response = await axios.post(
        'https://us-central1-foreclosurefinderbackend.cloudfunctions.net/fetch_data',
        req.body,
        { headers: { 'Content-Type': 'application/json' } }
        );
        res.status(response.status).send(response.data);
    } catch (error) {
        console.error('Error invoking Cloud Function:', error.response ? error.response.data : error.message);
        res.status(500).send('Error invoking Cloud Function');
    }
});

async function callPythonFunction(query) {
    try {
        console.log('Calling Python Cloud Function with:', query);
        // Call Cloud Function
        const response = await axios.post(
            'https://us-central1-foreclosurefinderbackend.cloudfunctions.net/fetch_data',
            query, 
            { headers: { 'Content-Type': 'application/json' } }
          );
        
        if (response.status === 200) {
            const responseData = response.data;
            console.log('Received response from Python Cloud Function:', responseData);
            updateProgress(responseData);
            return responseData;
        } else {
            console.error(`Error calling Python function: ${response.status} - ${response.statusText}`);
            return null;
        }
    } catch (error) {
        console.error("Error calling Python function:", error.message);
        return null;
    }
}

function updateProgress(data) {
    const lines = data.toString().split("\n");
    lines.forEach((line) => {
        try {
            console.log("Reached updateProgess"); // Log received lines
            const progressMatch = line.match(/{"progress":([^}]*)}/);
            if (progressMatch && progressMatch[1] !== null) {
                progressData = { progress: progressMatch[1] };
                console.log("Received progressData from Python: ", progressData); // Log received lines
            }
            const fileInfoMatch = line.match(/{"\s*type\s*":\s*"fileInfo"\s*,\s*"fileName"\s*:\s*"([^"]*)"\s*,\s*"fileUrl"\s*:\s*"([^"]*)"\s*}/);
            if (fileInfoMatch && fileInfoMatch[1] !== null) {
                const filename = fileInfoMatch[1];
                const fileUrl = fileInfoMatch[2];
                fileInfoData = { filename, fileUrl };
                console.log("Received fileInfoData from Python: ", filename); // Log received lines
                console.log("Received fileInfoData from Python: ", fileUrl); // Log received lines
            }
        } catch (error) {
            console.error("Error parsing data:", error);
        }
    });
}

app.use((req, res) => {
    return res.status(404).send("Not Found");
});

const server = app.listen(8080, () => {
    console.log(`HTTP Server is listening on localhost:8080`);
});

module.exports = server; 