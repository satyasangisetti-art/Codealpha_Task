# CodeAlpha Task 1 — Web Scraping Report

## 1. Objective
Collect a structured book dataset from the Books to Scrape educational website using Python and BeautifulSoup.

## 2. Tools used
- Python
- Requests
- BeautifulSoup
- Pandas (optional for subsequent analysis)
- CSV / Microsoft Excel
- GitHub

## 3. Methodology
1. Sent HTTP GET requests to listing pages.
2. Parsed the returned HTML.
3. Extracted book titles, prices, availability, ratings, and URLs using CSS selectors.
4. Followed the next-page link to navigate through pagination.
5. Optionally visited product pages for category, UPC, and description.
6. Removed duplicate product URLs and exported records to CSV.

## 4. Results
Fill this section from `output/scraping_summary.txt` after running the script.

- Run date:
- Listing pages visited:
- Unique records collected:
- Records with valid prices:
- Average listed price (GBP):
- Output file:

## 5. Data quality checks
Record the results after inspecting your CSV:
- Missing titles:
- Missing product URLs:
- Duplicate product URLs:
- Invalid prices:
- Ratings outside 1–5:
- Number of rows manually compared with source pages:

## 6. Challenges and solutions
Document any issues actually encountered, such as selector changes, temporary network failures, or missing optional detail fields. Do not claim issues or results that did not occur.

## 7. Conclusion
Summarize what you learned about HTML structure, CSS selectors, pagination, request handling, structured datasets, and responsible scraping.

## 8. Evidence
Add screenshots of the successful terminal run, a few rows of the CSV, and the GitHub repository.
