"""
Search Handler Module
Fetches real-time data from free search engines
"""

import time
import requests
from typing import List, Dict, Optional, Callable, Any
from bs4 import BeautifulSoup
import streamlit as st

# Import the renamed package
try:
    from ddgs import DDGS
except ImportError:
    # Fallback for older package name
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


class SearchHandler:
    """Handles real-time data fetching from search engines"""
    
    def __init__(self):
        self.ddgs = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self._init_ddgs()
    
    def _init_ddgs(self):
        """Initialize DuckDuckGo search"""
        if DDGS is None:
            st.warning("Search functionality unavailable. Install 'ddgs' package.")
            return
        
        try:
            self.ddgs = DDGS()
        except Exception as e:
            st.warning(f"Search initialization warning: {e}")
            self.ddgs = None
    
    # =========================================
    # 🔧 Error Handling Wrapper (Improvement 1)
    # =========================================
    def _safe_search(
        self, 
        search_func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Wrapper for safe search execution with error handling
        
        Args:
            search_func: The search function to execute
            *args: Positional arguments for the search function
            **kwargs: Keyword arguments for the search function
            
        Returns:
            Search results or empty list on failure
        """
        try:
            if not self.ddgs:
                self._init_ddgs()
            
            if self.ddgs:
                return search_func(*args, **kwargs)
            return []
        except Exception as e:
            error_msg = str(e)[:100]
            st.warning(f"Search temporarily unavailable: {error_msg}")
            return []
    
    # =========================================
    # 🔄 Retry Logic (Improvement 2)
    # =========================================
    def _search_with_retry(
        self, 
        search_func: Callable,
        query: str,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Execute search with retry logic
        
        Args:
            search_func: The search function to execute
            query: Search query string
            max_retries: Maximum retry attempts (default: self.max_retries)
            **kwargs: Additional arguments for the search function
            
        Returns:
            Search results or empty list after all retries fail
        """
        retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(retries):
            try:
                if not self.ddgs:
                    self._init_ddgs()
                
                if not self.ddgs:
                    return []
                
                results = search_func(query, **kwargs)
                
                if results:
                    return results
                    
            except Exception as e:
                last_error = e
                
                if attempt < retries - 1:
                    # Wait before retrying (exponential backoff)
                    wait_time = self.retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                else:
                    # Log error on final attempt
                    st.warning(f"Search failed after {retries} attempts: {str(e)[:50]}")
        
        return []
    
    # =========================================
    # 🔍 Core Search Methods
    # =========================================
    def search_web(
        self,
        query: str,
        max_results: int = 10,
        region: str = "wt-wt",
        use_retry: bool = True
    ) -> List[Dict]:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            region: Region for search results
            use_retry: Whether to use retry logic
            
        Returns:
            List of search results
        """
        def _execute_search(q, **kw):
            return list(self.ddgs.text(
                keywords=q,
                region=kw.get('region', 'wt-wt'),
                safesearch="moderate",
                max_results=kw.get('max_results', 10)
            ))
        
        if use_retry:
            return self._search_with_retry(
                _execute_search, 
                query,
                region=region,
                max_results=max_results
            )
        else:
            return self._safe_search(
                _execute_search,
                query,
                region=region,
                max_results=max_results
            )
    
    def search_news(
        self,
        query: str,
        max_results: int = 10,
        time_range: str = "w",
        use_retry: bool = True
    ) -> List[Dict]:
        """
        Search for news articles
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            time_range: Time range (d=day, w=week, m=month)
            use_retry: Whether to use retry logic
            
        Returns:
            List of news results
        """
        def _execute_search(q, **kw):
            return list(self.ddgs.news(
                keywords=q,
                region="wt-wt",
                safesearch="moderate",
                timelimit=kw.get('time_range', 'w'),
                max_results=kw.get('max_results', 10)
            ))
        
        if use_retry:
            return self._search_with_retry(
                _execute_search,
                query,
                time_range=time_range,
                max_results=max_results
            )
        else:
            return self._safe_search(
                _execute_search,
                query,
                time_range=time_range,
                max_results=max_results
            )
    
    def search_images(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search for images
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            
        Returns:
            List of image results
        """
        def _execute_search():
            return list(self.ddgs.images(
                keywords=query,
                region="wt-wt",
                safesearch="moderate",
                max_results=max_results
            ))
        
        return self._safe_search(_execute_search)
    
    def get_instant_answer(self, query: str) -> Optional[Dict]:
        """
        Get instant answer from DuckDuckGo
        
        Args:
            query: Search query string
            
        Returns:
            Instant answer dict or None
        """
        def _execute_search():
            results = self.ddgs.answers(query)
            if results:
                return results[0] if isinstance(results, list) else results
            return None
        
        return self._safe_search(_execute_search)
    
    # =========================================
    # 🌐 Additional Data Fetching Methods
    # =========================================
    def fetch_page_content(
        self, 
        url: str, 
        timeout: int = 10
    ) -> Optional[str]:
        """
        Fetch and parse content from a URL
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Extracted text content or None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text(separator=' ', strip=True)
                
                # Limit to first 5000 characters
                return text[:5000]
            return None
        except Exception as e:
            st.warning(f"Page fetch error: {str(e)[:50]}")
            return None
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Get basic market/stock data
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Market data dict or None
        """
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                chart = data.get('chart', {}).get('result', [{}])[0]
                meta = chart.get('meta', {})
                
                return {
                    'symbol': symbol,
                    'price': meta.get('regularMarketPrice'),
                    'previous_close': meta.get('previousClose'),
                    'currency': meta.get('currency'),
                    'exchange': meta.get('exchangeName')
                }
            return None
        except Exception as e:
            st.warning(f"Market data error: {str(e)[:50]}")
            return None
    
    def get_weather_data(self, location: str) -> Optional[Dict]:
        """
        Get weather data for a location
        
        Args:
            location: Location name
            
        Returns:
            Weather data dict or None
        """
        try:
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('current_condition', [{}])[0]
                
                return {
                    'location': location,
                    'temperature_c': current.get('temp_C'),
                    'temperature_f': current.get('temp_F'),
                    'condition': current.get('weatherDesc', [{}])[0].get('value'),
                    'humidity': current.get('humidity'),
                    'wind_speed': current.get('windspeedKmph')
                }
            return None
        except Exception as e:
            st.warning(f"Weather data error: {str(e)[:50]}")
            return None
    
    # =========================================
    # 📊 Data Compilation Methods
    # =========================================
    def compile_research_data(
        self,
        topic: str,
        include_news: bool = True,
        include_web: bool = True,
        include_instant: bool = True
    ) -> str:
        """
        Compile research data from multiple sources
        
        Args:
            topic: Research topic
            include_news: Include news results
            include_web: Include web results
            include_instant: Include instant answers
            
        Returns:
            Compiled research data as formatted string
        """
        compiled_data = []
        
        # Web search results
        if include_web:
            with st.spinner("Searching web..."):
                web_results = self.search_web(topic, max_results=5)
                
            if web_results:
                compiled_data.append("## 🌐 Web Search Results\n")
                for i, result in enumerate(web_results, 1):
                    title = result.get('title', 'No title')
                    body = result.get('body', 'No description')
                    href = result.get('href', '')
                    
                    compiled_data.append(f"### {i}. {title}")
                    compiled_data.append(f"{body}")
                    compiled_data.append(f"*Source: {href}*\n")
        
        # News results
        if include_news:
            with st.spinner("Searching news..."):
                news_results = self.search_news(topic, max_results=5)
                
            if news_results:
                compiled_data.append("\n## 📰 Recent News\n")
                for i, result in enumerate(news_results, 1):
                    title = result.get('title', 'No title')
                    date = result.get('date', 'Unknown date')
                    body = result.get('body', 'No description')
                    source = result.get('source', 'Unknown source')
                    
                    compiled_data.append(f"### {i}. {title}")
                    compiled_data.append(f"*{date} | {source}*")
                    compiled_data.append(f"{body}\n")
        
        # Instant answer
        if include_instant:
            instant = self.get_instant_answer(topic)
            if instant:
                compiled_data.append("\n## 💡 Quick Facts\n")
                if isinstance(instant, dict):
                    compiled_data.append(instant.get('text', str(instant)))
                else:
                    compiled_data.append(str(instant))
        
        # Return compiled data
        if compiled_data:
            return "\n".join(compiled_data)
        else:
            return f"No research data found for: {topic}"
    
    def compile_quick_facts(self, topic: str) -> Dict[str, Any]:
        """
        Compile quick facts about a topic
        
        Args:
            topic: Topic to research
            
        Returns:
            Dictionary with compiled facts
        """
        facts = {
            'topic': topic,
            'web_results': [],
            'news_results': [],
            'instant_answer': None,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Get web results
        web_results = self.search_web(topic, max_results=3)
        if web_results:
            facts['web_results'] = [
                {
                    'title': r.get('title', ''),
                    'snippet': r.get('body', '')[:200],
                    'url': r.get('href', '')
                }
                for r in web_results
            ]
        
        # Get news
        news_results = self.search_news(topic, max_results=3)
        if news_results:
            facts['news_results'] = [
                {
                    'title': r.get('title', ''),
                    'date': r.get('date', ''),
                    'source': r.get('source', '')
                }
                for r in news_results
            ]
        
        # Get instant answer
        instant = self.get_instant_answer(topic)
        if instant:
            facts['instant_answer'] = instant.get('text', str(instant)) if isinstance(instant, dict) else str(instant)
        
        return facts
    
    # =========================================
    # 🛠️ Utility Methods
    # =========================================
    def is_available(self) -> bool:
        """Check if search functionality is available"""
        return self.ddgs is not None
    
    def reset(self):
        """Reset the search handler"""
        self.ddgs = None
        self._init_ddgs()
    
    def get_status(self) -> Dict[str, Any]:
        """Get handler status information"""
        return {
            'available': self.is_available(),
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'ddgs_initialized': self.ddgs is not None
        }
