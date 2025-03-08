Analizando tu código con detalle, he identificado algunos patrones que se repiten y podrían extraerse en funciones auxiliares para mejorar la reutilización. Aquí están las principales duplicaciones:

### 1. Manejo de respuestas API

En varios métodos que interactúan con la API (`search_wikipedia`, `get_page_raw_text`, `get_page_links`, `get_page_categories`), hay patrones repetidos:

```python
# Este patrón se repite en múltiples métodos
if "error" in data:
    error_info = data["error"].get("info", "Unknown error in Wikipedia API")
    self.logger.error(f"Error in Wikipedia API: {error_info}")
    raise SearchError(f"API Error: {error_info}")
```

Podrías crear una función auxiliar como:

```python
def _check_api_errors(self, data, query_description):
    """Checks for errors in Wikipedia API responses.
    
    Args:
        data: API response data as a dictionary.
        query_description: String describing the current operation.
        
    Raises:
        WikiScraperError: If the API response contains an error.
    """
    if "error" in data:
        error_info = data["error"].get("info", "Unknown error in Wikipedia API")
        error_code = data["error"].get("code", "unknown")
        self.logger.error(f"Wikipedia API error: {error_info} | Code: {error_code}")
        raise WikiScraperError(f"API Error [{query_description}]: {error_info} (Code: {error_code})")

```

### 2. Construcción de parámetros API

Cada método que usa la API construye parámetros similares:

```python
params = {
    "action": "query",
    "format": "json",
    "titles": page_title,
    # ... otros parámetros específicos
}
```

Podrías tener una función base:

```python
def _build_base_api_params(self, **kwargs):
    """Builds base parameters for Wikipedia API requests.
    
    Args:
        **kwargs: Additional parameters to include in the request.
        
    Returns:
        dict: Dictionary containing API request parameters.
    """
    params = {
        "action": "query",
        "format": "json"
    }
    params.update(kwargs)
    return params
```

### 3. Manejo de excepciones HTTP

Este patrón se repite en varios métodos:

```python
except requests.HTTPError as http_err:
    status_code = getattr(http_err.response, "status_code", "N/A")
    reason = getattr(http_err.response, "reason", "Unknown HTTP error")
    self.logger.error(f"HTTP error {status_code}: {reason} retrieving X from '{page_title}'")
    raise WikiScraperError(f"HTTP Error: {status_code} - {reason}") from http_err
```

Podrías crear:

```python
def _handle_http_error(self, error, operation_description):
    """Handles HTTP errors with consistent logging.
    
    Args:
        error: The HTTP error exception.
        operation_description: String describing the current operation.
        
    Raises:
        WikiScraperError: A wrapper exception with formatted error details.
    """
    status_code = getattr(error.response, "status_code", "N/A")
    reason = getattr(error.response, "reason", "Unknown HTTP error")
    self.logger.error(f"HTTP error {status_code}: {reason} - {operation_description}")
    raise WikiScraperError(f"HTTP Error: {status_code} - {reason}") from error

```

### 4. Extracción de datos de páginas

En varios métodos (`get_page_categories`, `get_page_links`), hay lógica similar para extraer datos de la estructura de la respuesta:

```python
query_data = data.get("query", {})
pages_data = query_data.get("pages", {})

if not pages_data:
    # Manejo de páginas no encontradas
```

Podrías extraer:

```python
def _extract_pages_data(self, data, page_title):
    """Extracts page data from an API response.
    
    Args:
        data: API response data as a dictionary.
        page_title: Title of the Wikipedia page.
        
    Returns:
        dict: Dictionary containing page data.
        
    Raises:
        NoSearchResultsError: If the page is not found.
    """
    query_data = data.get("query", {})
    pages_data = query_data.get("pages", {})
    
    if not pages_data or "-1" in pages_data:
        self.logger.warning(f"Page not found: '{page_title}'")
        raise NoSearchResultsError(f"Page '{page_title}' does not exist")
        
    return pages_data
```

### 5. Paginación

La lógica de paginación se repite en métodos como `get_page_links` y `get_page_categories`:

```python
continue_data = data.get("continue")
if continue_data:
    continue_token = continue_data.get("KEY_NAME")
    self.logger.debug(f"Continuing pagination with token: {continue_token}")
else:
    break
```

Podrías implementar una función más genérica para manejar paginación:

```python
def _handle_pagination(self, data, token_key):
    """Extracts continuation tokens for API pagination.
    
    Args:
        data: API response data as a dictionary.
        token_key: Key name for the continuation token.
        
    Returns:
        str or None: Continuation token if available, otherwise None.
    """
    continue_data = data.get("continue")
    if not continue_data:
        return None
        
    token = continue_data.get(token_key)
    if token:
        self.logger.debug(f"Continuing pagination with token: {token}")
    return token
```

Implementando estas refactorizaciones, reducirías significativamente la duplicación de código, mejorarías la mantenibilidad y harías que el código sea más resistente a cambios futuros en la API de Wikipedia.