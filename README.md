# 🏠 Foreclosure Finder

Welcome to the Foreclosure Finder project! Currently in a bare bones state, this web application helps users find information about foreclosures using a simple API scraper.

This repository contains the Foreclosure Finder web application code. It utilizes Node.js, Express, WebSocket, and Python to provide real-time data for home foreclosures and auctions.

Future updates will focus on expanding API options and front-end GUI. 

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Usage](#usage)
  - [Making API Calls](#making-api-calls)
- [Contributing](#contributing)
- [License](#license)

## Getting Started

### Prerequisites

Before running the application, make sure you have the following tools installed on your machine:

- [Node.js](https://nodejs.org/)
- [npm (Node Package Manager)](https://www.npmjs.com/)
- [Python](https://www.python.org/)
- [Visual Studio Code](https://code.visualstudio.com/)

### Installation

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/madswitchman/foreclosure-finder-backend.git
   ```

2. Navigate to the project directory:

   ```bash
   cd foreclosure-finder-backend
   ```

3. Install Node.js dependencies:

   ```bash
   npm install
   ```

### Running the Application

Start the server:

```bash
npm start
```

This will run the application on `http://localhost:3000`.

## Usage

### Making API Calls

To initiate the foreclosure data scraping process, make a GET request to the following endpoint:

```
http://localhost:3000/run-script?state=AL&sortByEndingSoonest=true
```

As of now, only two API parameters are available.  
`state` - Two letter abbreviation of US State you wish to search (AL, AK, AZ, etc.)

`sortByEndingSoonest` - Listings are sorted by soonest ending (true, false)

## Contributing

If you'd like to contribute to this project, please follow the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the [GNU General Public License, v3](LICENSE).