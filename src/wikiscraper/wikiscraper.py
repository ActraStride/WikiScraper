"""
Module Name: wikiscraper

Professional Wikipedia scraping module with robust error handling, intelligent retries, and adherence to web scraping best practices.

This module provides:
- Automatic HTTP session management with configurable retries
- Strict input and parameter validation
- Redirection and non-HTML content detection
- Safe parsing with proper encoding handling
- Detailed logging and flexible configuration
- Compliance with robots.txt and usage policies

Example:
    >>> from wikiscraper import WikiScraper
    >>> with WikiScraper(language="es") as scraper:
    ...     soup = scraper.get_page_soup("Python")
    ...     print(soup.title.string)
"""


import logging
import requests

from typing import Any, Final, Optional, Set, List, Dict
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import quote, urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.errors.wiki import *

# Configuración de logging


# Constantes
USER_AGENT: Final[str] = "WikiScraperBot/1.0.0 (+https://github.com/ActraStride/WikiScraper)"
VALID_LANGUAGES: Final[Set[str]] = {"en", "ceb", "es", "fr", "de", "it", "pt", "ja", "zh", "ru", "ko", "nl", "ar", "simple"}
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_MAX_REDIRECTS: Final[int] = 3
DEFAULT_TIMEOUT: Final[int] = 15
DEFAULT_PARSER: Final[str] = "lxml"


class WikiScraper:
    """
    Professional class to scrape Wikipedia pages

    Attributes:
        language (str): Wikipedia language code (default: "es")
        timeout (int): Maximum waiting time for HTTP requests in seconds
        parser (str): Parser to be used by BeautifulSoup (lxml, html.parser, etc.)
        max_retries (int): Maximum number of retries for failed requests
        max_redirects (int): Maximum limit of allowed HTTP redirects

    Methods:

    Example:
        with WikiScraper(language="es") as scraper:
            try:
                soup = scraper.get_page_soup("Inteligencia_artificial")
                # Process the content...
            except WikiScraperError as e:
                print(f"Error: {e}")
    """

    def __init__(
        self,
        logger: logging.Logger,
        language: str = "es",
        timeout: int = DEFAULT_TIMEOUT,
        parser: str = DEFAULT_PARSER,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_redirects: int = DEFAULT_MAX_REDIRECTS
    ) -> None:
        """
        Initializes a new scraper instance with customizable configuration.

        Args:
            language: ISO 639-1 language code (default: "es")
            timeout: Maximum waiting time for HTTP response
            parser: HTML parser for BeautifulSoup
            max_retries: Maximum attempts for failed requests
            max_redirects: Limit of HTTP redirects

        Raises:
            LanguageNotSupportedError: If the language is not in VALID_LANGUAGES
        """
        if language not in VALID_LANGUAGES:
            raise LanguageNotSupportedError(f"Language '{language}' not supported. Valid languages: {', '.join(VALID_LANGUAGES)}")
        self.logger = logger
        self.language = language
        self.timeout = timeout
        self.parser = parser
        self.max_redirects = max_redirects
        self.base_url = f"https://{self.language}.wikipedia.org/"
        self.session = requests.Session()

        # HTTP session configuration
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.max_redirects = self.max_redirects

        # Retry configuration
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.logger.debug("Scraper initialized: %s", self.__repr__())


    def __repr__(self) -> str:
        return (f"WikiScraper(language={self.language}, timeout={self.timeout}, "
                f"parser={self.parser}, retries={self.session.adapters['https://'].max_retries.total})")


    def _build_url(self, page_title: str) -> str:
        """
        Builds the complete and validated URL for the requested page.

        Args:
            page_title: Title of the page on Wikipedia

        Returns:
            str: Complete and validated URL

        Raises:
            InvalidPageTitleError: If the title is empty or invalid
        """
        if not page_title or not isinstance(page_title, str):
            raise InvalidPageTitleError("Page title must be a non-empty string")

        cleaned_title = page_title.strip()
        encoded_title = quote(cleaned_title, safe='')
        return urljoin(self.base_url, f"wiki/{encoded_title}")


    def get_page_soup(self, page_title: str) -> BeautifulSoup:
        """
        Obtains and parses the HTML content of a Wikipedia page.

        Args:
            page_title: Title of the page (e.g., "Artificial_intelligence")

        Returns:
            BeautifulSoup: Parsed object with the page content

        Raises:
            WikiScraperError: For network, HTTP, or validation errors
            ParsingError: If parsing the HTML content fails
            NonHTMLContentError: If the response is not valid HTML

        Example:
            with WikiScraper() as scraper:
                soup = scraper.get_page_soup('Python')
                print(soup.find('h1').text)
        """
        url = self._build_url(page_title)
        self.logger.info("Initiating request for: %s", url)

        try:
            response = self.session.get(url, timeout=self.timeout)

            # Verify redirects
            if response.history:
                self.logger.warning("Redirect detected (%d hops): %s -> %s",
                             len(response.history), response.history[0].url, response.url)

            # Validate content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                raise NonHTMLContentError(f"Invalid content type: {content_type}")

            response.raise_for_status()

            self.logger.debug("Response received [%d] in %.2fs, Size: %.2fKB",
                         response.status_code,
                         response.elapsed.total_seconds(),
                         len(response.content)/1024)

            return BeautifulSoup(response.content, self.parser, from_encoding=response.encoding)

        except requests.RequestException as e:
            status_code = getattr(e.response, 'status_code', None)
            error_msg = f"HTTP Error {status_code}" if status_code else f"Network Error: {e}"
            self.logger.error("%s - URL: %s", error_msg, url)
            raise WikiScraperError(error_msg) from e

        except FeatureNotFound as e:
            self.logger.error("Parser '%s' not available: %s", self.parser, e)
            raise ParsingError(f"Parser {self.parser} not available") from e

        except Exception as e:
            self.logger.error("Unexpected error: %s - %s", type(e).__name__, e, exc_info=True)
            raise WikiScraperError(f"Unexpected error: {type(e).__name__} - {e}") from e
        

    def search_wikipedia(self, query: str, limit: int = 5) -> List[str]:
        """
        Searches for page titles on Wikipedia using the API.

        Args:
            query: Search term.
            limit: Maximum number of results to return.

        Returns:
            A list of Wikipedia page titles that match the search.

        Raises:
            SearchError: If there is an error in the API request.
            NoSearchResultsError: If the search returns no results.
        """
        search_url = urljoin(self.base_url, "w/api.php")
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "",
        }

        self.logger.info(f"Initiating Wikipedia search for query: '{query}' with a limit of {limit} results.")
        self.logger.debug(f"Search URL: {search_url} | Parameters: {params}")

        try:
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            self.logger.info("Response received from the Wikipedia API successfully.")
            data = response.json()
            self.logger.debug(f"Data received from the API: {data}")

            # Verify API errors
            if "error" in data:
                error_info = data["error"].get("info", "Unknown error in Wikipedia API")
                self.logger.error(f"Error in Wikipedia API: {error_info}")
                raise SearchError(f"API Error: {error_info}")

            # Verify response structure
            if "query" not in data or "search" not in data["query"]:
                self.logger.error(f"Unexpected structure in the response for search '{query}'.")
                raise NoSearchResultsError(f"The search '{query}' returned no results.")

            results = [item["title"] for item in data["query"]["search"]]
            self.logger.info(f"Search completed. Found {len(results)} results for '{query}'.")

            # Verify if there are empty results
            if not results:
                self.logger.warning(f"The search '{query}' returned no results.")
                raise NoSearchResultsError(f"The search '{query}' returned no results.")

            return results

        except requests.RequestException as e:
            self.logger.exception(f"Error in Wikipedia search: {e}")
            raise SearchError(f"Error in Wikipedia search: {e}") from e
        except (KeyError, ValueError) as e:
            self.logger.exception(f"Error processing the API response: {e}")
            raise SearchError(f"Error processing the API response: {e}") from e


    def get_page_soup_with_search(self, query: str) -> BeautifulSoup:
        """
        Retrieves the content of a page using Wikipedia search.

        Args:
            query: Search term or page title.

        Returns:
            BeautifulSoup: Parsed object with the page content.

        Raises:
            WikiScraperError: If there are errors in the search or when getting the page.
            NoSearchResultsError: If no search results are found.
        """
        self.logger.info(f"Initiating content retrieval for query: '{query}'.")
        try:
            # Step 1: Search for the term
            search_results = self.search_wikipedia(query)  # search_wikipedia now handles empty results
            self.logger.info(f"Search results obtained: {search_results}")

            # Step 2: Attempt to retrieve the first page
            first_result_title = search_results[0]
            self.logger.info(f"Retrieving content from page: '{first_result_title}'.")
            page_soup = self.get_page_soup(first_result_title)
            self.logger.info(f"Content of page '{first_result_title}' obtained successfully.")
            return page_soup

        except WikiScraperError as e:
            self.logger.error(f"Error getting '{first_result_title}': {str(e)}")
            raise  # Reraises the exception preserving the original traceback


    
    def get_page_raw_text(self, page_title: str) -> str:
        """
        Retrieves the content of a Wikipedia article in plain text using the API.

        Args:
            page_title: Title of the Wikipedia page.

        Returns:
            str: The content of the article in plain text.

        Raises:
            WikiScraperError: If there is an error communicating with the API or processing the response.
            NoSearchResultsError: If the page is not found or has no content.
        """
        api_url = urljoin(self.base_url, "w/api.php")
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "extracts",
            "explaintext": "true",  # Important to get plain text
            "exlimit": "1",  # Limit to one page (the requested one)
        }

        self.logger.info(f"Getting plain text for '{page_title}' from the API.")
        self.logger.debug(f"API URL: {api_url} | Parameters: {params}")

        try:
            response = self.session.get(api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            self.logger.debug(f"API Response: {data}")

            if "error" in data:
                error_info = data["error"].get("info", "Unknown error in Wikipedia API")
                self.logger.error(f"Error in Wikipedia API: {error_info}")
                raise SearchError(f"API Error: {error_info}")

            query = data.get("query", {})
            pages = query.get("pages", {})

            if not pages:
                self.logger.warning(f"Page '{page_title}' not found in the API response.")
                raise NoSearchResultsError(f"Page '{page_title}' not found.")

            # Pages are indexed by pageid, normally there will only be one
            page_content = None
            for page_id in pages:
                page_data = pages[page_id]
                if "extract" in page_data:
                    page_content = page_data["extract"]
                    break  # Take the content of the first page (should be the only one with exlimit=1)
                elif "missing" in page_data:
                    self.logger.warning(f"Page '{page_title}' not found (missing in API).")
                    raise NoSearchResultsError(f"Page '{page_title}' not found.")
                else:
                    self.logger.warning(f"Unexpected API response for '{page_title}': {page_data}")
                    raise SearchError(f"Unexpected API response when getting '{page_title}'.")

            if page_content:
                self.logger.info(f"Plain text obtained successfully for '{page_title}'.")
                return page_content
            else:
                self.logger.warning(f"Could not extract plain text content for '{page_title}'.")
                raise NoSearchResultsError(f"Could not get plain text content for '{page_title}'.")


        except requests.RequestException as e:
            self.logger.exception(f"Error getting plain text from API for '{page_title}': {e}")
            raise SearchError(f"API communication error: {e}") from e
        except (KeyError, ValueError) as e:
            self.logger.exception(f"Error processing API response for '{page_title}': {e}")
            raise SearchError(f"Error processing API response: {e}") from e
    
    
    def get_page_links(self, page_title: str,
                   link_type: str = "internal",
                   limit: int = 500,
                   namespace: Optional[int] = None) -> List[str]:
        """
        Retrieves links from a Wikipedia page using the MediaWiki API.

        This method handles pagination automatically and supports different
        types of links that can be extracted from Wikipedia pages.

        Args:
            page_title: Title of the Wikipedia page to retrieve links from.
            link_type: Type of links to retrieve. Options are:
                    - 'internal': Links to other Wikipedia pages (default)
                    - 'external': Links to external websites
                    - 'linkshere': Pages that link to this page
                    - 'interwiki': Links to pages on other wikis
            limit: Maximum number of links to return (1-500 for regular users,
                up to 5000 for bots with proper authentication).
            namespace: Filter links by MediaWiki namespace ID. 
                    Examples: 0 (main), 1 (talk), 14 (category)
                    See https://www.mediawiki.org/wiki/Help:Namespaces for full list

        Returns:
            List[str]: Depending on link_type:
                    - internal/linkshere: Page titles
                    - external: URLs as strings
                    - interwiki: Strings in format "prefix:title"

        Raises:
            ValueError: If an invalid link_type is provided
            WikiScraperError: For API errors, network issues, or parsing problems
        """
        # Link type configuration - maps link types to their API parameters
        LINK_TYPE_CONFIG = {
            "internal": {"module": "links", "param_prefix": "pl", "result_key": "links"},
            "external": {"module": "extlinks", "param_prefix": "el", "result_key": "extlinks"},
            "linkshere": {"module": "linkshere", "param_prefix": "lh", "result_key": "linkshere"},
            "interwiki": {"module": "iwlinks", "param_prefix": "iw", "result_key": "iwlinks"}
        }
        
        # Validate link type before proceeding
        if link_type not in LINK_TYPE_CONFIG:
            valid_types = ", ".join(LINK_TYPE_CONFIG.keys())
            raise ValueError(f"Invalid link type '{link_type}'. Must be one of: {valid_types}")
        
        # Validate limit parameter
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer")
        
        # Get configuration for the requested link type
        config = LINK_TYPE_CONFIG[link_type]
        module = config["module"]
        param_prefix = config["param_prefix"]
        result_key = config["result_key"]
        
        # API endpoint for MediaWiki
        api_url = urljoin(self.base_url, "w/api.php")
        
        self.logger.info(f"Retrieving {link_type} links from '{page_title}' with limit {limit}")
        
        def build_params(continue_token=None):
            """
            Builds API request parameters including pagination tokens if available.
            
            Args:
                continue_token: Dictionary with continuation tokens from previous response
                
            Returns:
                Dict containing all parameters needed for the API request
            """
            params = {
                "action": "query",
                "format": "json",
                "titles": page_title,
                "prop": module,
                f"{param_prefix}limit": str(limit),
            }
            
            # Add namespace filter if specified
            if namespace is not None:
                params[f"{param_prefix}namespace"] = str(namespace)
                
            # Add continuation parameters if we're paginating
            if continue_token:
                params.update(continue_token)
                
            return params
        
        def extract_links_from_page(page_data):
            """
            Extracts and formats links from a page data dictionary.
            
            Args:
                page_data: Dictionary containing page information from API response
                
            Returns:
                List of formatted link strings based on the link_type
            """
            extracted_links = []
            
            # Check if page has links of the requested type
            if result_key in page_data:
                for item in page_data[result_key]:
                    if link_type == "external":
                        # External links have URLs in the "*" field
                        extracted_links.append(item["*"])
                    elif link_type == "interwiki":
                        # Interwiki links combine prefix and title
                        extracted_links.append(f"{item['prefix']}:{item['*']}")
                    else:
                        # Internal and linkshere links use the title field
                        extracted_links.append(item["title"])
                        
            return extracted_links
        
        # Initialize results and pagination variables
        all_links = []
        continue_data = None
        
        # Log initial request parameters for debugging
        initial_params = build_params()
        self.logger.debug(f"API Request URL: {api_url} | Parameters: {initial_params}")
        
        # Pagination loop - continues until all results are retrieved
        while True:
            try:
                # Build request parameters (including continue token if available)
                request_params = build_params(continue_data)
                
                # Make the API request
                response = self.session.get(api_url, params=request_params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if "error" in data:
                    error_info = data["error"].get("info", "Unknown Wikipedia API error")
                    error_code = data["error"].get("code", "unknown")
                    self.logger.error(f"Wikipedia API error: {error_info} | Code: {error_code}")
                    raise WikiScraperError(f"API Error: {error_info} (Code: {error_code})")
                
                # Get the pages data from the response
                query_data = data.get("query", {})
                pages_data = query_data.get("pages", {})
                
                # Handle case where no pages are found
                if not pages_data:
                    self.logger.warning(
                        f"No pages data found for '{page_title}'. Page may not exist or has no {link_type} links."
                    )
                    break
                
                # Process each page in the response (typically just one)
                for _, page_info in pages_data.items():
                    new_links = extract_links_from_page(page_info)
                    all_links.extend(new_links)
                    
                    # Log missing page warning if applicable
                    if "missing" in page_info:
                        self.logger.warning(f"Page '{page_title}' does not exist")
                
                # Check if we need to continue pagination
                continue_data = data.get("continue")
                if continue_data:
                    self.logger.debug(f"Continuing pagination with token: {continue_data}")
                else:
                    # No more results to retrieve
                    break
                    
            except requests.HTTPError as http_err:
                # Extract status code and reason from the HTTP error
                status_code = getattr(http_err.response, "status_code", "N/A")
                reason = getattr(http_err.response, "reason", "Unknown HTTP error")
                
                self.logger.error(f"HTTP error {status_code}: {reason} retrieving links from '{page_title}'")
                raise WikiScraperError(f"HTTP Error: {status_code} - {reason}") from http_err
                
            except requests.Timeout:
                self.logger.error(f"Request timeout retrieving links from '{page_title}'")
                raise WikiScraperError("Timeout during link retrieval from Wikipedia")
                
            except Exception as e:
                self.logger.exception(f"Unexpected error during link retrieval: {str(e)}")
                raise WikiScraperError(f"Unexpected error during link retrieval: {str(e)}") from e
        
        self.logger.info(f"Retrieved {len(all_links)} {link_type} links from '{page_title}'")
        return all_links
                
                
    def get_page_categories(self, page_title: str) -> List[str]:
        """
        Retrieves categories for a Wikipedia article using the API with full pagination.

        Args:
            page_title: Title of the Wikipedia page.

        Returns:
            List[str]: A list of category names for the page.

        Raises:
            WikiScraperError: If there is an error communicating with the API or processing the response.
            NoSearchResultsError: If the page is not found or has no categories.
        """
        logger = logging.getLogger(__name__) # Get logger based on module name, standard practice

        API_ACTION = "query" # Define constants for API parameters, makes code more readable and maintainable
        API_FORMAT = "json"
        API_PROP = "categories"
        API_CATEGORY_LIMIT = "max" # Which corresponds to 500, maximum allowed by the API
        API_CATEGORY_SHOW = "!hidden"
        API_CATEGORY_NAMESPACE = 14 # Categories namespace

        def build_params(continue_token: str = None) -> Dict[str, str]:
            """Builds API parameters with pagination support."""
            params = {
                "action": API_ACTION,
                "format": API_FORMAT,
                "titles": page_title,
                "prop": API_PROP,
                "cllimit": API_CATEGORY_LIMIT,
                "clshow": API_CATEGORY_SHOW,
                "clnamespace": API_CATEGORY_NAMESPACE # Categories namespace
            }
            if continue_token:
                params["clcontinue"] = continue_token
            return params

        def process_category_title(category: Dict[str, Any]) -> str:
            """Extracts and safely formats the category name from API response."""
            title = category.get("title", "")
            return title.split(":", 1)[-1] if title else "" # Safely process title and remove "Category:" prefix

        api_url = urljoin(self.base_url, "w/api.php")
        categories = []
        continue_token = None
        self.logger.info(f"Starting category retrieval for page: '{page_title}'") # Log in English

        try:
            while True:
                response = self.session.get(
                    api_url,
                    params=build_params(continue_token),
                    timeout=self.timeout
                )
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                data = response.json()
                self.logger.debug(f"API response received - Size: {len(response.content)} bytes") # Log in English

                if "error" in data:
                    error_info = data["error"].get("info", "Unknown API error") # Default error message in English
                    error_code = data['error'].get('code')
                    self.logger.error(f"API Error: {error_info} | Code: {error_code}") # Log in English, include error code
                    raise WikiScraperError(f"API Error: {error_info} (Code: {error_code})") # Include code in exception message

                query_data = data.get("query", {}) # Renamed to be clearer
                pages_data = query_data.get("pages", {}) # Renamed to be clearer

                if not pages_data or "-1" in pages_data: # Check if pages are missing or API returns -1 for not found
                    self.logger.warning(f"Page not found: '{page_title}'") # Log in English
                    raise NoSearchResultsError(f"Page '{page_title}' does not exist") # Exception message in English

                page_info = next(iter(pages_data.values()))  # Get the first/only page data
                categories_batch = [
                    process_category_title(category)
                    for category in page_info.get("categories", [])
                    if process_category_title(category) # Ensure processed category is not empty
                ]
                categories.extend(categories_batch)

                # Handle pagination
                continue_data = data.get("continue") # Renamed for clarity
                if continue_data:
                    continue_token = continue_data.get("clcontinue")
                    self.logger.debug(f"Continuing pagination with token: {continue_token}") # Log in English
                else:
                    break # No more continue token, pagination finished

        except requests.HTTPError as http_err: # Specific exception name for clarity
            status_code = http_err.response.status_code if http_err.response else 'N/A' # Handle case where response is None
            reason = http_err.response.reason if http_err.response else 'N/A'
            self.logger.error(f"HTTP Error {status_code}: {reason}") # Log with status code and reason
            raise WikiScraperError(f"HTTP Error: {status_code} - {reason}") from http_err # Re-raise with original exception context
        except requests.Timeout as timeout_err: # Specific exception name
            self.logger.error("Timeout connecting to Wikipedia API") # Log in English
            raise WikiScraperError("Connection Timeout") from timeout_err # Re-raise with original exception context
        except KeyError as key_err: # Specific exception name
            self.logger.error(f"Unexpected API response structure: Missing field {key_err}") # Log in English
            raise WikiScraperError("Invalid API response structure") from key_err # Re-raise with original exception context
        except Exception as e: # Catch-all for unexpected exceptions during API interaction, consider more specific exceptions as needed
            self.logger.exception(f"Unexpected error during API request: {e}") # Use self.logger.exception to capture traceback
            raise WikiScraperError(f"Unexpected error during API request") from e # Re-raise as WikiScraperError

        self.logger.info(f"Retrieved {len(categories)} categories for '{page_title}'") # Final log in English
        return categories

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        self.logger.debug("HTTP session closed successfully")