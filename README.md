# Insomnia.gr Scraper
Python BS4 scrapper for high-tech forum insomnia.gr

## Overview

This script scrapes user and comment data from the high-tech forum insomnia.gr. It leverages BeautifulSoup and Requests to efficiently extract and process the forum's content.
Scrapped data can be used for differente purposes, such as data handling, database testing, osint, etc.

## Key Features

* Downloads insomnia.gr's sitemap to retrieve thread URLs.
* Downloads insomnia.gr's members info.
* Creates a version control file to maintain scraping progress.
* Iterates through thread comments, extracting user names, comment content, and timestamps.
* Stores extracted data in JSON format under the `~/output/` directory.
* Provides a user-friendly command-line interface for specifying scraping options.
* Returns database specs
* Can get sample data

## Available Options

* `--download-all`: Downloads all threads from insomnia.gr.
* `--update`: Updates the existing database.
* `--members`: Gets or updates the user database.
* `--version-control`: Gets only the version control file.
* `--sample`: Gets 100 random threads for testing.
* `--working-directory`: Choose either the database `[output]` or the sample database `[sample]` to search.
* `--info`: Returns database/sample information (number of threads, total size).
* `--check`: Checks if a specific thread ID exists in the database/sample.
* `--ts`: Returns the ts of a specific thread ID.
  
## Installation and Setup

### Prerequisites

* Python 3.x
* Requests library
* BeautifulSoup library
* tqdm

### Installation

Install the required libraries using pip:
   ```bash
   pip install requests beautifulsoup4
   ```


### Running the Script

1. Place the insomnia_scraper.py file in your desired working directory.
2. Open a terminal and navigate to the working directory.
3. Execute the following command, providing any desired scraping options:
```bash
   python insomnia_scraper.py --options
```

## Example Usage:

* To scrape all threads from insomnia.gr and save the data to a JSON file named data.json under the ~/output/ directory:

```bash
python insomnia_scraper.py --download-all
```
Usage
The script handles thread retrieval and version control automatically. It generates a version control json file that records the last processed thread's URL and timestamp. Subsequent scraping runs will resume.


* To download insomnia.gr's members:
```bash
python insomnia_scrapper.py -m
```
Usage
The script opens a webbrowser session for the user to get the latest member. After inserting the latest member, the sripts downloads all new member since the last users_db update. 


* To check if thread_id 589656 is in the database:
```bash
python insomnia_scrapper.py -c 589656 -w output

```


