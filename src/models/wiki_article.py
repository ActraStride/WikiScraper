from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class WikipediaSection:
    """
    Data model representing a section within a Wikipedia article.
    
    Attributes:
        title (str): Section heading text
        content (str): Plain text content of the section
        level (int): Hierarchical level (1 for main sections, 2+ for subsections)
        subsections (List['WikipediaSection']): Nested subsections within this section
    """
    title: str
    content: str
    level: int
    subsections: List['WikipediaSection'] = None
    
    def __post_init__(self):
        """Initialize empty list for subsections if not provided"""
        if self.subsections is None:
            self.subsections = []
    
    def __str__(self) -> str:
        """
        Provides human-readable string representation of the section.
        
        Returns:
            Section title as string identifier
        """
        return self.title

@dataclass
class WikipediaArticle:
    """
    Comprehensive data model representing a Wikipedia article.
    
    Encapsulates all relevant article information including content structure,
    metadata, cross-references, and multilingual availability.
    
    Attributes:
        title (str): Article title
        page_id (int): Unique Wikipedia page identifier
        summary (str): Concise article summary
        content (str): Full article text content
        url (str): Canonical Wikipedia URL
        last_edited (datetime): Timestamp of most recent edit
        sections (List[WikipediaSection]): Hierarchical content sections
        categories (List[str]): Associated categorization tags
        links (List[str]): Internal Wikipedia article links
        external_links (List[str]): External website references
        images (List[str]): Embedded image URLs
        references (List[str]): Citation sources
        infobox (Dict[str, str]): Structured key-value data table
        languages (Dict[str, str]): Available language versions (ISO code → URL)
    """
    title: str
    page_id: int
    summary: str
    content: str
    url: str
    last_edited: datetime
    sections: List[WikipediaSection]
    categories: List[str]
    links: List[str]
    external_links: List[str]
    images: List[str]
    references: List[str]
    infobox: Dict[str, str]
    languages: Dict[str, str]
    
    def __str__(self) -> str:
        """
        Standard string representation for quick identification.
        
        Returns:
            Formatted string containing title and URL
        """
        return f"WikipediaArticle(title={self.title}, url={self.url})"
    
    def get_section(self, section_title: str) -> Optional[WikipediaSection]:
        """
        Recursively retrieves a section by its title.
        
        Performs case-insensitive search through all sections and subsections.
        
        Args:
            section_title: Target section heading text
            
        Returns:
            Matched WikipediaSection object or None if not found
        """
        def search_in_sections(sections, title):
            for section in sections:
                if section.title.lower() == title.lower():
                    return section
                
                if section.subsections:
                    result = search_in_sections(section.subsections, title)
                    if result:
                        return result
            return None
        
        return search_in_sections(self.sections, section_title)
    
    def has_category(self, category: str) -> bool:
        """
        Determines article membership in a specified category.
        
        Args:
            category: Category name to verify
            
        Returns:
            True if article belongs to category, False otherwise
        """
        return any(cat.lower() == category.lower() for cat in self.categories)
    
    def count_references(self) -> int:
        """
        Calculates total number of bibliographic references.
        
        Returns:
            Count of reference entries
        """
        return len(self.references)
    
    def get_main_sections(self) -> List[WikipediaSection]:
        """
        Retrieves top-level sections of the article.
        
        Returns:
            List of level 1 WikipediaSection objects
        """
        return [section for section in self.sections if section.level == 1]
    
    def get_translation_url(self, language_code: str) -> Optional[str]:
        """
        Retrieves localized version URL for specified language.
        
        Args:
            language_code: ISO 639 language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            URL string for target language version, or None if unavailable
        """
        return self.languages.get(language_code)