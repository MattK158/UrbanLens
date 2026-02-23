import httpx
import time
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

SOCRATA_BASE_URL = "https://data.austintexas.gov/resource"
APP_TOKEN = os.getenv("AUSTIN_API_APP_TOKEN", "")
PAGE_SIZE = 1000
MAX_PAGES = 500  # Safety cap — never pull more than 500k records per run

def get_headers():
    headers = {"Accept": "application/json"}
    if APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    return headers

def fetch_dataset(
    dataset_id: str,
    where_clause: Optional[str] = None,
    order_by: str = ":id",
    max_pages: int = MAX_PAGES,
):
    """
    Fetches all records from a Socrata dataset using pagination.
    Yields one page of records at a time.
    """
    url = f"{SOCRATA_BASE_URL}/{dataset_id}.json"
    offset = 0
    pages_fetched = 0

    while pages_fetched < max_pages:
        params = f"$limit={PAGE_SIZE}&$offset={offset}&$order={order_by}"

        if where_clause:
            params += f"&$where={where_clause}"

        try:
            response = httpx.get(
                f"{url}?{params}",
                headers=get_headers(),
                timeout=30.0
            )
            response.raise_for_status()
            records = response.json()

            if not records:
                break

            yield records

            if len(records) < PAGE_SIZE:
                break

            offset += PAGE_SIZE
            pages_fetched += 1

            # Be polite to the API — small delay between pages
            time.sleep(0.2)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                print(f"Server error at offset {offset}, retrying after delay...")
                time.sleep(5)
                continue
            print(f"HTTP error fetching {dataset_id}: {e}")
            raise
        except httpx.TimeoutException:
            print(f"Timeout fetching {dataset_id} at offset {offset}, retrying...")
            time.sleep(2)
            continue

def fetch_incremental(dataset_id: str, date_field: str, since: Optional[str] = None):
    """
    Fetches only records newer than `since` date.
    If since is None, fetches all records (full historical load).
    """
    where_clause = None
    if since:
        where_clause = f"{date_field} > '{since}'"

    yield from fetch_dataset(dataset_id, where_clause=where_clause, order_by=date_field)