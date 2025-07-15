# Walmart Product Seller Offers Scraper

A powerful Python tool to extract product SKU and seller offers from any Walmart product page. This script automates the process of gathering detailed seller information, including all available offers for a given product, and saves the results in a structured JSON file.

## Features

- **Automatic Dependency Installation**: Installs required Python packages on first run.
- **Robust Scraping**: Fetches product page, extracts SKU, and retrieves seller offers token.
- **Anti-bot Awareness**: Handles common anti-bot mechanisms and logs warnings if scraping is blocked.
- **Structured Output**: Saves all seller offers in a `result.json` file for easy analysis.
- **Informative Logging**: Uses colored logs for clear, real-time feedback during execution.

## Requirements

- Python 3.7+
- Internet connection

## Installation

No manual installation required! The script will automatically install the following dependencies if they are missing:

- `requests`
- `beautifulsoup4`
- `coloredlogs`

## Usage

1. **Clone or Download the Repository**

   ```bash
   git clone https://github.com/ssshipilo/walmart_scrape.git
   cd walmart_test
   ```

2. **Run the Script**

   ```bash
   python walmart.py
   ```

3. **Enter the Walmart Product URL**

   When prompted, paste the full URL of the Walmart product page you want to scrape. Example:

   ```
   Enter the product link: https://www.walmart.com/ip/LEGO-Technic-tbd-42200/6924164794
   ```

4. **View Results**

   After successful execution, the seller offers will be saved in `result.json` in the project directory.

## Example Output

```json
{
    "data": {
        "marketplace": {
            "offers": [
                {
                    "sellerName": "Example Seller",
                    "price": 49.99,
                    ...
                }
            ]
        }
    }
}
```

## How It Works

1. **Fetches the product page HTML** using a browser-like user agent.
2. **Extracts the SKU** from embedded JSON-LD data.
3. **Finds the seller offers token** from a dynamically loaded JavaScript chunk.
4. **Requests all seller offers** using the extracted SKU and token.
5. **Saves the offers** to `result.json`.

## Troubleshooting

- If you see warnings about anti-bot protection, try running the script again later or with a different product URL.
- Ensure your internet connection is stable.
- For persistent issues, check the logs for detailed error messages.

## License

This project is provided for educational and research purposes only. Use responsibly and respect Walmart's terms of service.

---

**Author:** SAV | shypilo.com
