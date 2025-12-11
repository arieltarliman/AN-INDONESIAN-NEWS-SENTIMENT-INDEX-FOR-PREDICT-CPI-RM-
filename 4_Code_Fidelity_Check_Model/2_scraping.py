import pandas as pd
import trafilatura
import requests
from urllib.parse import urlparse
import time
import random
import logging
from pathlib import Path
import json
from typing import Dict, Optional, Tuple
from datetime import datetime

# Configuration
class ScraperConfig:
    CHUNK_SIZE = 100  # Save after every N URLs
    MIN_DELAY = 2.0  # Minimum seconds between requests
    MAX_DELAY = 5.0  # Maximum seconds between requests
    TIMEOUT = 15  # Request timeout in seconds
    MAX_RETRIES = 3
    MIN_ARTICLE_LENGTH = 200  # Minimum characters for valid article
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101',
    ]
    
    # Patterns to skip (non-article pages)
    SKIP_PATTERNS = [
        '/foto/', '/photo/', '/gallery/', '/infografis/',
        '/video/', '/live/', '/breaking-news-live/',
        '/snippet/', '/opini-singkat/', '/sponsored/',
        '/advertorial/', '/promosi/'
    ]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = requests.Session()
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'by_source': {}
        }
        
    def should_skip_url(self, url: str) -> Tuple[bool, str]:
        """Check if URL should be skipped based on patterns."""
        url_lower = url.lower()
        
        for pattern in self.config.SKIP_PATTERNS:
            if pattern in url_lower:
                return True, f"matched skip pattern: {pattern}"
        
        return False, ""
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc.replace('www.', '')
        except:
            return 'unknown'
    
    def fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch URL content with retry logic."""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': random.choice(self.config.USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.config.TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response.text
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def extract_article(self, html: str, url: str) -> Optional[Dict[str, str]]:
        """Extract article content using trafilatura."""
        try:
            # Extract with trafilatura (handles multiple formats well)
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                favor_precision=True,
                url=url
            )
            
            if not extracted or len(extracted) < self.config.MIN_ARTICLE_LENGTH:
                return None
            
            # Get metadata
            metadata = trafilatura.extract_metadata(html)
            
            return {
                'text': extracted,
                'title': metadata.title if metadata and metadata.title else '',
                'author': metadata.author if metadata and metadata.author else '',
                'date': metadata.date if metadata and metadata.date else '',
                'description': metadata.description if metadata and metadata.description else ''
            }
            
        except Exception as e:
            logger.error(f"Extraction error for {url}: {str(e)}")
            return None
    
    def scrape_url(self, url: str) -> Dict:
        """Scrape a single URL and return result."""
        result = {
            'url': url,
            'status': 'failed',
            'domain': self.get_domain(url),
            'scraped_at': datetime.now().isoformat(),
            'text': None,
            'title': None,
            'author': None,
            'date': None,
            'description': None,
            'error': None
        }
        
        # Check if should skip
        should_skip, skip_reason = self.should_skip_url(url)
        if should_skip:
            result['status'] = 'skipped'
            result['error'] = skip_reason
            self.stats['skipped'] += 1
            logger.info(f"Skipped: {url} ({skip_reason})")
            return result
        
        # Fetch HTML
        html = self.fetch_with_retry(url)
        if not html:
            result['error'] = 'failed to fetch'
            self.stats['failed'] += 1
            logger.error(f"Failed to fetch: {url}")
            return result
        
        # Extract article
        article = self.extract_article(html, url)
        if not article:
            result['status'] = 'failed'
            result['error'] = 'extraction failed or content too short'
            self.stats['failed'] += 1
            logger.warning(f"Extraction failed: {url}")
            return result
        
        # Success
        result['status'] = 'success'
        result['text'] = article['text']
        result['title'] = article['title']
        result['author'] = article['author']
        result['date'] = article['date']
        result['description'] = article['description']
        self.stats['success'] += 1
        
        # Update domain stats
        domain = result['domain']
        if domain not in self.stats['by_source']:
            self.stats['by_source'][domain] = {'success': 0, 'failed': 0, 'skipped': 0}
        self.stats['by_source'][domain]['success'] += 1
        
        logger.info(f"Success: {url} ({len(article['text'])} chars)")
        return result
    
    def save_checkpoint(self, results: list, checkpoint_file: Path):
        """Save results to checkpoint file."""
        df = pd.DataFrame(results)
        df.to_csv(checkpoint_file, index=False, encoding='utf-8')
        logger.info(f"Checkpoint saved: {len(results)} records to {checkpoint_file}")
    
    def load_checkpoint(self, checkpoint_file: Path) -> Tuple[list, set]:
        """Load existing checkpoint and return results + processed URLs."""
        if checkpoint_file.exists():
            df = pd.read_csv(checkpoint_file)
            results = df.to_dict('records')
            processed_urls = set(df['url'].tolist())
            logger.info(f"Loaded checkpoint: {len(results)} existing records")
            return results, processed_urls
        return [], set()
    
    def scrape_dataset(
        self,
        df: pd.DataFrame,
        output_file: str = 'scraped_articles.csv',
        checkpoint_interval: int = None
    ):
        """Main scraping pipeline with resumable progress."""
        checkpoint_interval = checkpoint_interval or self.config.CHUNK_SIZE
        checkpoint_file = Path(output_file.replace('.csv', '_checkpoint.csv'))
        
        # Load existing progress
        results, processed_urls = self.load_checkpoint(checkpoint_file)
        
        # Filter URLs to process
        urls_to_process = [
            url for url in df['url'].tolist()
            if url not in processed_urls
        ]
        
        logger.info(f"Total URLs: {len(df)}")
        logger.info(f"Already processed: {len(processed_urls)}")
        logger.info(f"Remaining: {len(urls_to_process)}")
        
        self.stats['total'] = len(urls_to_process)
        
        # Process URLs
        for idx, url in enumerate(urls_to_process, 1):
            logger.info(f"Processing {idx}/{len(urls_to_process)}: {url}")
            
            # Scrape
            result = self.scrape_url(url)
            results.append(result)
            
            # Rate limiting
            delay = random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY)
            time.sleep(delay)
            
            # Save checkpoint
            if idx % checkpoint_interval == 0:
                self.save_checkpoint(results, checkpoint_file)
                self.print_stats()
        
        # Final save
        self.save_checkpoint(results, checkpoint_file)
        
        # Save final output
        final_df = pd.DataFrame(results)
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Final output saved to {output_file}")
        
        # Remove checkpoint file
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info("Checkpoint file removed")
        
        self.print_stats()
        return final_df
    
    def print_stats(self):
        """Print scraping statistics."""
        logger.info("=" * 60)
        logger.info(f"Total processed: {self.stats['success'] + self.stats['failed'] + self.stats['skipped']}")
        logger.info(f"Success: {self.stats['success']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        
        if self.stats['by_source']:
            logger.info("\nBy source:")
            for domain, counts in self.stats['by_source'].items():
                logger.info(f"  {domain}: {counts['success']} success, {counts['failed']} failed")
        logger.info("=" * 60)


if __name__ == "__main__":
    # Load dataset
    df = pd.read_csv('fidelity_check_model/data/NewsDataClean_fidelity.csv')
    
    # Initialize scraper
    config = ScraperConfig()
    scraper = NewsScraper(config)
    
    # Run scraping
    results_df = scraper.scrape_dataset(
        df,
        output_file='scraped_articles.csv',
        checkpoint_interval=50  # Save every 50 URLs
    )
    
    # Analyze results
    print("\nFinal Statistics:")
    print(results_df['status'].value_counts())
    print("\nBy domain:")
    print(results_df.groupby('domain')['status'].value_counts())