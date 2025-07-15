import subprocess
import sys

required_modules = {
    "requests": None,
    "bs4": "beautifulsoup4==4.13.4",
    "coloredlogs": None,
}

# Installing modules if they are not installed
for import_name, install_name in required_modules.items():
    try:
        __import__(import_name)
    except ImportError:
        module_to_install = install_name if install_name else import_name
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_to_install])

import re
import json
import uuid
import time
import string
import logging
import secrets
import requests
import urllib.parse
from typing import Optional

import coloredlogs
from bs4 import BeautifulSoup


class WalmartProductScraper:
    """
    Scraper to extract product SKU and seller offers token from Walmart product page.
    """

    def __init__(self, product_url: str) -> None:
        """
        Initialize scraper with product URL and setup logger.

        :param product_url: URL of the Walmart product page.
        """
        self.product_url = product_url
        self.session = requests.Session()
        self.sku: Optional[str] = None
        self.token: Optional[str] = None

        # Logger setup
        self.logger = logging.getLogger(' WalmartProductScraper ')
        coloredlogs.install(level='INFO', logger=self.logger)

    def fetch_page(self) -> Optional[str]:
        """
        Fetch the product page HTML content.

        :return: HTML content as string or None if request failed.
        """
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru,en-CA;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6,pl;q=0.5",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://www.walmart.com/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "script",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "cross-site",
            "sec-fetch-storage-access": "active",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        try:
            response = self.session.get(self.product_url, headers=headers)
            response.raise_for_status()
            self.logger.info("Fetched product page successfully.")
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch product page: {e}")
            return None

    def extract_sku(self, html: str) -> Optional[str]:
        """
        Extract the SKU from the JSON-LD script tag in HTML.

        :param html: HTML content of the product page.
        :return: SKU string or None if not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        script_tag = soup.find("script", {"type": "application/ld+json", "data-seo-id": "schema-org-product"})
        if not script_tag:
            self.logger.warning("JSON-LD script tag with product schema not found.")
            return None

        try:
            data = json.loads(script_tag.string)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON-LD content: {e}")
            return None

        if isinstance(data, list):
            for item in data:
                if 'sku' in item:
                    self.logger.info(f"SKU found: {item['sku']}")
                    return item['sku']
        elif isinstance(data, dict) and 'sku' in data:
            self.logger.info(f"SKU found: {data['sku']}")
            return data['sku']

        self.logger.warning("SKU field not found in JSON-LD data.")
        return None

    def find_token(self, html: str) -> Optional[str]:
        """
        Find the seller offers token from the JS chunk script.

        :param html: HTML content of the product page.
        :return: Token string or None if not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        pattern = re.compile(r"_next/static/chunks/marketplace_product-seller-info_product-seller-info-[a-zA-Z0-9]+\.js$")
        script_tag = soup.find("script", src=pattern)

        if not script_tag:
            self.logger.warning("Required <script> tag with product-seller-info not found.")
            return None

        # Construct JS URL for all sellers panel
        full_src = script_tag["src"]
        base_url = full_src.split("/_next/")[0]
        js_url = base_url + "/_next/static/chunks/marketplace_all-sellers-panel.f4a5450545d8ccfb.js"

        headers = {
            "accept": "*/*",
            "referer": self.product_url,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        try:
            js_response = self.session.get(js_url, headers=headers)
            js_response.raise_for_status()
            self.logger.info("Fetched JS file for token extraction successfully.")
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch JS file for token: {e}")
            return None

        pattern = r'const\s+\w+\s*=\s*{.*?},'
        matches = re.findall(pattern, js_response.text, re.DOTALL)

        for match in matches:
            obj_text = match[match.find('{'):match.rfind('}') + 1]
            json_like = re.sub(r'(\w+)\s*:', r'"\1":', obj_text)

            try:
                data = json.loads(json_like)
                if data.get("name") == "GetAllSellerOffers":
                    self.logger.info(f"Found token: {data.get('hash')}")
                    return data.get("hash")
            except json.JSONDecodeError:
                continue

        self.logger.warning("Token not found in JS file.")
        return None

    @staticmethod
    def generate_secure_random_string(length: int = 20) -> str:
        """
        Generate a secure random string for isomorphicSessionId.

        :param length: Length of the generated string.
        :return: Random string consisting of ascii letters, digits, and underscore.
        """
        chars = string.ascii_letters + string.digits + "_"
        return ''.join(secrets.choice(chars) for _ in range(length))

    def get_seller_offers(
        self,
        sku: str,
        token: str
    ) -> Optional[dict]:
        """
        Fetch seller offers using SKU and token.

        :param sku: SKU of the product.
        :param token: Token hash string.
        :return: Parsed JSON response or None if failed.
        """
        variables = {
            "itemId": sku,
            "isSubscriptionEligible": True,
            "conditionCodes": [1],
            "allOffersSource": "MORE_SELLER_OPTIONS"
        }
        compact_json = json.dumps(variables, separators=(',', ':'))
        encoded_variables = urllib.parse.quote(compact_json)
        final_url = (
            f"https://www.walmart.com/orchestra/home/graphql/GetAllSellerOffers/"
            f"{token}?variables={encoded_variables}"
        )

        isomorphic_session_id = self.generate_secure_random_string()
        render_view_id = str(uuid.uuid4())

        headers = {
            "accept": "application/json",
            "accept-language": "en-US",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "downlink": "10",
            "dpr": "1",
            "baggage": (
                f"trafficType=customer,deviceType=desktop,renderScope=SSR,"
                f"webRequestSource=Browser,pageName=itemPage,isomorphicSessionId={isomorphic_session_id},"
                f"renderViewId={render_view_id}"
            ),
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": final_url,
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "wm_mp": "true",
            "wm_page_url": final_url,
            "wm_qos.correlation_id": "EM0F5CQkMfg6w9Ral2ECqd05NaVpa-hzAaoh",
            "x-apollo-operation-name": "GetAllSellerOffers",
            "x-enable-server-timing": "1",
            "x-latency-trace": "1",
            "x-o-bu": "WALMART-US",
            "x-o-ccm": "server",
            "x-o-correlation-id": "EM0F5CQkMfg6w9Ral2ECqd05NaVpa-hzAaoh",
            "x-o-gql-query": "query GetAllSellerOffers",
            "x-o-mart": "B2C",
            "x-o-platform": "rweb",
            "x-o-platform-version": "usweb-1.212.0-3d45d91d0379181242084b528eb8317750d32b99-7102008r",
            "x-o-segment": "oaoh",
        }

        try:
            response = self.session.get(final_url, headers=headers)
            response.raise_for_status()
            self.logger.info("Fetched seller offers successfully.")
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch seller offers: {e}")
            return None

    def scrape(self) -> None:
        """
        Main method to run scraping sequence.
        """
        time_start = time.time()
        html = self.fetch_page()
        if not html:
            return

        self.sku = self.extract_sku(html)
        if not self.sku:
            return

        self.token = self.find_token(html)
        if not self.token:
            self.logger.warning("Unable to find token, possibly due to anti-bot protection.")
            return

        result = self.get_seller_offers(self.sku, self.token)
        if result:
            with open("result.json", "w", encoding="utf-8") as file:
                json.dump(result, file, indent=4, ensure_ascii=False)
            self.logger.info("Seller offers saved to result.json")
        else:
            self.logger.warning("Failed to retrieve seller offers.")

        df = time.time() - time_start
        print(f"We received information about the product in {df:.2f} seconds.")

if __name__ == "__main__":
    # https://www.walmart.com/ip/LEGO-Technic-tbd-42200/6924164794
    walmart_url = input("Enter the product link: ").strip()
    scraper = WalmartProductScraper(walmart_url)
    scraper.scrape()
