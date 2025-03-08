"""
Module Name: file_saver

Professional module for secure storage of scraped content. Provides functionality for:
- Safe file and directory handling
- Encoding control and filename validation
- Automatic output directory management
- Custom exceptions for storage error handling

Example:
    >>> from src.storage.file_saver import FileSaver
    >>> with FileSaver(output_dir="data", encoding="utf-8") as saver:
    ...     file_path = saver.save("Scraped content", title="Example")
    ...     print(f"File saved at: {file_path}")
"""

import logging
import re

from pathlib import Path
from datetime import datetime
from typing import Optional, Final
from urllib.parse import quote

# Constants
DEFAULT_OUTPUT_DIR: Final[str] = "data"
VALID_ENCODINGS: Final[tuple] = ('utf-8', 'latin-1', 'iso-8859-1')
MAX_FILENAME_LENGTH: Final[int] = 255
SAFE_FILENAME_PATTERN: Final[str] = r"[^A-Za-z0-9_\-\.]"


class StorageError(Exception):
    """Base class for storage related exceptions."""
    pass

class DirectoryCreationError(StorageError):
    """Raised when directory creation fails."""
    pass

class FileWriteError(StorageError):
    """Raised when writing to a file fails."""
    pass

class InvalidFilenameError(StorageError):
    """Raised when a filename is considered invalid or unsafe."""
    pass


class FileSaver:
    """
    Class for secure storage of textual content with automatic directory management
    and filename generation.

    Attributes:
        output_dir (Path): Base directory for storage.
        encoding (str): File encoding (default: 'utf-8').
        timestamp_format (str): Format for timestamps in filenames.

    Methods:
        save(content: str, title: Optional[str] = None) -> Path: Saves content to a file.
        generate_filename(title: Optional[str] = None) -> str: Generates a filename.
        sanitize_filename(filename: str) -> str: Sanitizes a filename to be safe.
    """

    def __init__(
        self,
        logger: logging.Logger,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        encoding: str = 'utf-8',
        timestamp_format: str = "%Y%m%d_%H%M%S"
    ) -> None:
        """
        Initializes the FileSaver with customizable settings.

        Args:
            logger (logging.Logger): Logger instance for logging messages.
            output_dir (str, optional): Base directory for storage. Defaults to DEFAULT_OUTPUT_DIR ("data").
            encoding (str, optional): Text encoding for the files. Defaults to 'utf-8'.
            timestamp_format (str, optional): strftime format for filenames. Defaults to "%Y%m%d_%H%M%S".

        Raises:
            DirectoryCreationError: If the output directory cannot be created.
            ValueError: If the specified encoding is not supported.
        """
        self.output_dir = Path(output_dir)
        self.timestamp_format = timestamp_format
        self.logger = logger

        if encoding.lower() not in VALID_ENCODINGS:
            raise ValueError(f"Unsupported encoding: {encoding}. Use one of: {', '.join(VALID_ENCODINGS)}")
        self.encoding = encoding.lower()

        self._setup_storage()

        
    def _setup_storage(self) -> None:
        """Sets up the output directory for file storage.

        Creates the output directory if it does not already exist.
        Handles potential `PermissionError` and `OSError` exceptions
        during directory creation, logging critical errors and raising
        `DirectoryCreationError` in case of failure.

        Raises:
            DirectoryCreationError: If the directory cannot be created due to
                permissions issues or other system errors.
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Storage directory ready: {self.output_dir}")
        except PermissionError as e:
            self.logger.critical(f"Permission denied for: {self.output_dir}")
            raise DirectoryCreationError(f"Permission error: {e}") from e
        except OSError as e:
            self.logger.critical(f"Error creating directory: {e}")
            raise DirectoryCreationError(f"System error: {e}") from e
            

    def sanitize_filename(self, filename: str) -> str:
        """Sanitizes a filename to remove unsafe characters and limit length.

        Removes characters not allowed in filenames, replaces spaces with
        underscores, and truncates the filename to the maximum allowed length.

        Args:
            filename: The original filename string.

        Returns:
            str: The sanitized and safe filename.

        Raises:
            InvalidFilenameError: If the sanitized filename is empty.
        """
        # Replace unsafe characters with underscores
        clean_name = re.sub(SAFE_FILENAME_PATTERN, "_", filename)

        # Strip leading/trailing whitespace, replace internal spaces with underscores, and truncate
        clean_name = clean_name.strip().replace(" ", "_")[:MAX_FILENAME_LENGTH]

        if not clean_name:
            raise InvalidFilenameError("Filename is invalid after sanitization (empty string)")

        return clean_name
    

    def generate_filename(self, title: Optional[str] = None) -> str:
        """Generates a unique filename based on title and timestamp.

        Creates a filename by combining a timestamp with a sanitized
        version of the provided title, if available. If no title is
        provided or if the title results in an invalid filename after
        sanitization, a default filename is generated using the timestamp
        and a generic name.

        Args:
            title: Optional title to include in the filename. If provided,
                   it will be sanitized to ensure filename safety.

        Returns:
            str: A valid generated filename.
        """
        timestamp = datetime.now().strftime(self.timestamp_format)

        if title:
            try:
                safe_title = self.sanitize_filename(quote(title))
                return f"{timestamp}_{safe_title}.txt"
            except InvalidFilenameError:
                self.logger.warning("Invalid title provided, using default filename.")

        return f"{timestamp}_wikipedia_content.txt"
    

    def save(self, content: str, title: Optional[str] = None) -> Path:
        """Saves the content to a text file with specified encoding.

        Generates a filename using `generate_filename`, creates the file within
        the output directory, and writes the given content to it. Handles
        potential `IOError` and `UnicodeEncodeError` exceptions during
        file writing. After successful save, it performs a post-save validation.

        Args:
            content: The textual content to be saved.
            title: Optional title to be used for filename generation.

        Returns:
            Path: The full path to the saved file.

        Raises:
            FileWriteError: If writing to the file fails due to IO or encoding errors.
        """
        filename = self.generate_filename(title)
        file_path = self.output_dir / filename

        try:
            with open(file_path, "w", encoding=self.encoding, errors="replace") as f:
                f.write(content)

            self.logger.info(f"Successfully saved file: {file_path}")
            self._post_save_validation(file_path, content)
            return file_path

        except IOError as e:
            self.logger.error(f"Error writing file (IOError): {e}", exc_info=True)
            raise FileWriteError(f"I/O error during file write: {e}") from e
        except UnicodeEncodeError as e:
            self.logger.error(f"Error encoding content to file: {e}", exc_info=True)
            raise FileWriteError(f"Encoding error during file write: {e}") from e
            

    def _post_save_validation(self, file_path: Path, original_content: str) -> None:
        """Performs post-save validation to ensure file integrity.

        Reads the content back from the saved file and compares it to the
        original content to detect any discrepancies that might indicate
        data corruption during the saving process. Logs a warning if a
        discrepancy is found, and logs an error if there's an issue reading
        the saved file for validation.

        Args:
            file_path: Path to the saved file to be validated.
            original_content: The original content that was intended to be saved.
        """
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                saved_content = f.read()

            if saved_content != original_content:
                self.logger.warning("Content discrepancy detected after save. Possible data corruption.")

        except IOError as e:
            self.logger.error(f"Error validating saved file: {e}")


    def __enter__(self):
        """Allows FileSaver to be used as a context manager.

        Returns:
            FileSaver: Returns the instance of FileSaver, allowing it to be
                       used within a 'with' statement.
        """
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handles the context exit for FileSaver.

        Currently, no specific resource cleanup is needed, so this method
        simply passes.  It is available for future implementation of resource
        management if required.

        Args:
            exc_type: Exception type if an exception occurred within the context, otherwise None.
            exc_val: Exception value if an exception occurred, otherwise None.
            exc_tb: Exception traceback if an exception occurred, otherwise None.
        """
        pass  # Resource cleanup can be implemented here if necessary


    def __repr__(self) -> str:
        """Returns a string representation of the FileSaver object.

        Provides a representation that includes the output directory,
        encoding, and timestamp format, useful for debugging and logging.

        Returns:
            str: String representation of the FileSaver instance.
        """
        return (f"FileSaver(output_dir={self.output_dir}, "
                f"encoding={self.encoding}, "
                f"timestamp_format={self.timestamp_format})")