# NZB Completion Checker

A fast, concurrent command-line utility to verify the availability of all articles in an NZB file on a Usenet server *before* you start downloading.

## Why Use This?

Have you ever started downloading a large multi-gigabyte file from Usenet, only to discover hours later that it's missing too many articles to be repaired? This script solves that problem.

By performing a "pre-flight check," it quickly queries your provider for every article listed in the NZB file without downloading the full article bodies. This saves you significant time and bandwidth by letting you know upfront if a download is worth starting.

## Features

-   **High Performance:** Uses Python's `asyncio` to handle dozens or hundreds of concurrent connections, checking articles in parallel.
-   **Bandwidth Efficient:** Utilizes the NNTP `STAT` command to check only for an article's existence, not its content, saving hundreds of kilobytes per check.
-   **Configurable:** Easily set the number of concurrent connections to match your provider's limits.
-   **User-Friendly:** A real-time progress bar shows the status, followed by a clear summary report of found, missing, and errored articles.
-   **Cross-Platform:** Runs on any system with Python 3.

## Prerequisites

-   Python 3.8+
-   `pip` and `venv` for managing dependencies. On Debian/Ubuntu, ensure you have `python3-venv` installed (`sudo apt install python3.11-venv`).

## Installation

1.  **Clone the repository (or download the script):**
    ```bash
    git clone https://your-repo-url/nzb-completion-checker.git
    cd nzb-completion-checker
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *On Windows, use `venv\Scripts\activate`*

3.  **Install the required packages:**
    Create a file named `requirements.txt` with the following content:
    ```
    tqdm
    ```
    Then, run the installation command:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The script is run from the command line with several optional arguments.

```bash
usage: nzb_checker.py [-h] -s SERVER [-p PORT] [-u USERNAME] [-pw PASSWORD]
                      [-c CONNECTIONS] [--no-ssl] [--show-missing]
                      nzb_file

A fast, concurrent Usenet NZB completion checker.

positional arguments:
  nzb_file              Path to the .nzb file to check.

options:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        Usenet server address (e.g., news.your-provider.com).
  -p PORT, --port PORT  Server port (default: 563 for SSL).
  -u USERNAME, --username USERNAME
                        Your Usenet username.
  -pw PASSWORD, --password PASSWORD
                        Your Usenet password.
  -c CONNECTIONS, --connections CONNECTIONS
                        Number of concurrent connections to use (default: 50).
  --no-ssl              Disable SSL for the connection (e.g., for port 119).
  --show-missing        Print the list of all missing article IDs at the end.
