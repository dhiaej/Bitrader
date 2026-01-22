"""
Crypto News Service
Fetches latest crypto news from CoinDesk API (or returns empty if not configured).
Rate limited to ~15 requests/hour (11k/month limit).
Includes persistent file-based caching for fallback.
"""
from typing import Dict, List
import time
import requests
import json
import os
from pathlib import Path

from config import settings


class NewsService:
    def __init__(self) -> None:
        self.api_key = settings.COINDESK_API_KEY
        # CoinDesk RSS feed (working) - try this first
        # Fallback to API endpoints if RSS fails
        self.base_urls = [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",  # RSS feed (working)
            "https://data.coindesk.com/v1/news",  # API endpoint (may not exist)
            "https://api.coindesk.com/v1/news",  # Alternative API endpoint
        ]
        # Simple in-memory cache: {symbol: (news_items, timestamp)}
        # Cache expires after 5 minutes to keep news fresh while respecting rate limits
        self._cache: Dict[str, tuple[List[Dict], float]] = {}
        self._cache_ttl = 300  # 5 minutes (300 seconds) - well within 15 requests/hour limit
        
        # Rate limiting: Track requests per hour
        # 11k/month = ~366/day = ~15/hour = ~1 every 4 minutes
        self._request_times: List[float] = []
        self._max_requests_per_hour = 12  # Conservative limit (slightly below 15)
        
        # File-based cache for persistent fallback
        # Store cache file in backend directory
        backend_dir = Path(__file__).parent.parent
        self._cache_file = backend_dir / "news_cache.json"

    def _map_symbol(self, symbol: str) -> str:
        # "BTC-USD" -> "BTC"
        parts = symbol.upper().split("-")
        return parts[0] if parts else symbol.upper()
    
    def _load_file_cache(self) -> Dict[str, List[Dict]]:
        """Load news cache from JSON file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[NEWS] Loaded file cache with {len(data)} symbols")
                    return data
        except Exception as e:
            print(f"[NEWS] Error loading file cache: {e}")
        return {}
    
    def _save_file_cache(self, cache_data: Dict[str, List[Dict]]) -> None:
        """Save news cache to JSON file."""
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"[NEWS] Saved file cache with {len(cache_data)} symbols")
        except Exception as e:
            print(f"[NEWS] Error saving file cache: {e}")

    def _check_rate_limit(self) -> bool:
        """Check if we can make a request based on rate limits."""
        current_time = time.time()
        # Remove requests older than 1 hour
        self._request_times = [t for t in self._request_times if current_time - t < 3600]
        
        if len(self._request_times) >= self._max_requests_per_hour:
            oldest_request = min(self._request_times)
            wait_time = 3600 - (current_time - oldest_request)
            print(f"[NEWS] Rate limit reached. Wait {int(wait_time/60)} minutes before next request.")
            return False
        return True

    def get_symbol_news(self, symbol: str, limit: int = 5, force_refresh: bool = False) -> List[Dict]:
        if not self.api_key:
            # Not configured; caller can treat as "no news"
            print(f"[NEWS] COINDESK_API_KEY not configured - news will not be fetched")
            return []

        cache_key = symbol.upper()
        
        # Store old titles for comparison (before clearing cache if force_refresh)
        old_titles_for_comparison = set()
        if cache_key in self._cache:
            old_items, _ = self._cache[cache_key]
            old_titles_for_comparison = {item.get("title", "") for item in old_items}
        
        # If force_refresh is True, clear all caches
        if force_refresh:
            print(f"[NEWS] Force refresh requested for {cache_key} - clearing all caches")
            if cache_key in self._cache:
                del self._cache[cache_key]
            # Clear file cache entry
            file_cache = self._load_file_cache()
            if cache_key in file_cache:
                del file_cache[cache_key]
                self._save_file_cache(file_cache)
        
        # Check cache first (unless force refresh)
        if not force_refresh and cache_key in self._cache:
            cached_items, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                print(f"[NEWS] Returning cached news for {cache_key} ({len(cached_items)} items)")
                return cached_items
            else:
                # Cache expired, remove it
                del self._cache[cache_key]

        # Check rate limit before making API call
        if not self._check_rate_limit():
            # Return expired cache if available
            if cache_key in self._cache:
                cached_items, _ = self._cache[cache_key]
                print(f"[NEWS] Rate limited - returning expired cache ({len(cached_items)} items)")
                return cached_items
            # Try file cache as fallback
            file_cache = self._load_file_cache()
            if cache_key in file_cache:
                cached_items = file_cache[cache_key]
                print(f"[NEWS] Rate limited - returning file cache ({len(cached_items)} items)")
                return cached_items
            return []

        try:
            currency = self._map_symbol(symbol)
            print(f"[NEWS] Fetching news for {currency} (symbol: {symbol})")
            
            # Try each endpoint until one works
            for base_url in self.base_urls:
                try:
                    # CoinDesk API request - try different auth methods
                    headers = {}
                    if self.api_key:
                        # Try different header formats
                        headers["X-API-Key"] = self.api_key
                        headers["Authorization"] = f"Bearer {self.api_key}"
                    
                    params = {
                        "limit": limit,
                    }
                    
                    # For RSS feeds, add cache-busting and proper headers
                    if "rss" in base_url:
                        # Add timestamp query parameter to force fresh RSS feed
                        params = {"_": int(time.time())}  # Cache-busting timestamp
                        # Add cache-busting headers to force fresh RSS feed
                        headers.update({
                            "Cache-Control": "no-cache, no-store, must-revalidate",
                            "Pragma": "no-cache",
                            "Expires": "0",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        })
                    
                    print(f"[NEWS] Trying CoinDesk endpoint: {base_url}")
                    # Increased timeout to 5 seconds for better reliability
                    resp = requests.get(base_url, headers=headers, params=params, timeout=5)
                    print(f"[NEWS] Response status: {resp.status_code}")
                    
                    # Track this request for rate limiting
                    self._request_times.append(time.time())
                    
                    if resp.status_code == 429:
                        print(f"[NEWS] ERROR: Rate limited by CoinDesk API (429 Too Many Requests)")
                        # If we have cached data (even expired), return it as fallback
                        if cache_key in self._cache:
                            cached_items, _ = self._cache[cache_key]
                            print(f"[NEWS] Returning expired cache as fallback ({len(cached_items)} items)")
                            return cached_items
                        continue  # Try next endpoint
                    
                    if resp.status_code != 200:
                        print(f"[NEWS] Endpoint returned status {resp.status_code}, trying next...")
                        continue
                    
                    # Parse response
                    if "rss" in base_url or resp.headers.get("content-type", "").startswith("application/rss") or resp.headers.get("content-type", "").startswith("text/xml"):
                        # Parse RSS feed (simplified - using basic XML parsing)
                        news_items = self._parse_rss_feed(resp.text, limit, currency)
                        if news_items:
                            # Check if news actually changed by comparing titles
                            # Use old_titles_for_comparison which was stored before cache clear
                            new_titles = {item.get("title", "") for item in news_items}
                            
                            if old_titles_for_comparison and old_titles_for_comparison == new_titles:
                                print(f"[NEWS] RSS feed returned same news items for {currency} (no new articles - {len(new_titles)} items unchanged)")
                            elif old_titles_for_comparison:
                                # Calculate what's new
                                new_article_count = len(new_titles - old_titles_for_comparison)
                                print(f"[NEWS] SUCCESS: Parsed {len(news_items)} news items from RSS feed for {currency} ({new_article_count} NEW articles detected)")
                            else:
                                print(f"[NEWS] SUCCESS: Parsed {len(news_items)} news items from RSS feed for {currency} (initial fetch)")
                            
                            # Always update cache with latest data (even if same, to refresh timestamp)
                            self._cache[cache_key] = (news_items, time.time())
                            # Save to file cache for persistent fallback
                            file_cache = self._load_file_cache()
                            file_cache[cache_key] = news_items
                            self._save_file_cache(file_cache)
                        return news_items
                    else:
                        # Parse JSON response
                        data = resp.json()
                        print(f"[NEWS] Response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                        
                        # Handle different response formats
                        if isinstance(data, dict):
                            results = data.get("data", data.get("results", data.get("articles", data.get("items", []))))
                        elif isinstance(data, list):
                            results = data
                        else:
                            results = []
                        
                        print(f"[NEWS] Found {len(results)} total results, limiting to {limit}")
                        results = results[:limit]

                        news_items: List[Dict] = []
                        for item in results:
                            # Handle different API response formats
                            title = item.get("title") or item.get("headline") or item.get("name") or ""
                            url = item.get("url") or item.get("link") or item.get("article_url") or item.get("href")
                            source = item.get("source") or item.get("source_name") or "CoinDesk"
                            published_at = item.get("published_at") or item.get("published") or item.get("date") or item.get("created_at")
                            
                            if not title:
                                continue
                            
                            # Determine impact based on keywords in title
                            impact = self._determine_impact(title, item.get("metadata", {}))
                            
                            news_items.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "source": source,
                                    "published_at": published_at,
                                    "impact": impact,
                                }
                            )
                            print(f"[NEWS] Added news: {title[:50]}... (impact: {impact})")

                        print(f"[NEWS] SUCCESS: Fetched {len(news_items)} news items for {currency} from {base_url}")
                        # Cache the results in memory
                        self._cache[cache_key] = (news_items, time.time())
                        # Save to file cache for persistent fallback
                        file_cache = self._load_file_cache()
                        file_cache[cache_key] = news_items
                        self._save_file_cache(file_cache)
                        return news_items
                        
                except requests.exceptions.Timeout:
                    print(f"[NEWS] Timeout with endpoint {base_url} (non-blocking)")
                    continue
                except requests.exceptions.ConnectionError as e:
                    print(f"[NEWS] Connection error with endpoint {base_url}: {e} (non-blocking)")
                    continue
                except Exception as e:
                    print(f"[NEWS] Error with endpoint {base_url}: {e} (non-blocking)")
                    continue
            
            # All endpoints failed - try file cache as fallback
            print(f"[NEWS] All endpoints failed, checking file cache...")
            file_cache = self._load_file_cache()
            if cache_key in file_cache:
                cached_items = file_cache[cache_key]
                print(f"[NEWS] Returning file cache as fallback ({len(cached_items)} items)")
                return cached_items
            print(f"[NEWS] No file cache available, returning empty list")
            return []
            
        except Exception as e:
            import traceback
            print(f"[NEWS] ERROR: Error fetching news for {symbol}: {e}")
            print(f"[NEWS] Traceback: {traceback.format_exc()}")
            # Try file cache as last resort
            try:
                file_cache = self._load_file_cache()
                if cache_key in file_cache:
                    cached_items = file_cache[cache_key]
                    print(f"[NEWS] Exception occurred - returning file cache ({len(cached_items)} items)")
                    return cached_items
            except:
                pass
            return []
    
    def _parse_rss_feed(self, rss_content: str, limit: int, currency: str) -> List[Dict]:
        """Parse RSS feed content (simplified XML parsing)."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(rss_content)
            news_items: List[Dict] = []
            
            # Find all items in RSS
            items = root.findall(".//item")[:limit]
            for item in items:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                
                title = title_elem.text if title_elem is not None else ""
                url = link_elem.text if link_elem is not None else ""
                published_at = pub_date_elem.text if pub_date_elem is not None else ""
                
                if title:
                    impact = self._determine_impact(title, {})
                    news_items.append({
                        "title": title,
                        "url": url,
                        "source": "CoinDesk",
                        "published_at": published_at,
                        "impact": impact,
                    })
            
            print(f"[NEWS] Parsed {len(news_items)} items from RSS feed")
            return news_items
        except Exception as e:
            print(f"[NEWS] Error parsing RSS: {e}")
            return []

    def _determine_impact(self, title: str, metadata: Dict) -> str:
        """
        Determine news impact level based on keywords and metadata.
        Returns: 'high', 'medium', or 'low'
        """
        title_lower = title.lower()
        
        # Check metadata importance if available
        importance = metadata.get("importance")
        if importance:
            # Some APIs use 1-3 scale, map to our levels
            if importance == 3 or importance == "high":
                return "high"
            elif importance == 2 or importance == "medium":
                return "medium"
            else:
                return "low"
        
        # High-impact keywords (regulatory, major events, hacks, major announcements)
        high_impact_keywords = [
            "regulation", "regulatory", "ban", "banned", "prohibition", "illegal",
            "sec", "sec approval", "sec rejects", "sec lawsuit", "sec sues",
            "etf approval", "etf rejected", "etf launch", "spot etf",
            "hack", "hacked", "exploit", "breach", "stolen", "theft",
            "crash", "crashed", "collapse", "plunge", "meltdown",
            "approval", "approved", "legal", "legalized", "adoption",
            "halving", "halvening", "fork", "hard fork",
            "bankruptcy", "bankrupt", "liquidation", "insolvent",
            "federal reserve", "fed", "interest rate", "rate hike", "rate cut",
            "china ban", "china bans", "government", "president", "congress",
            "bill", "law", "legislation", "act",
        ]
        
        # Medium-impact keywords
        medium_impact_keywords = [
            "partnership", "partners", "integration", "launch", "listing",
            "upgrade", "update", "announcement", "news", "report",
            "price", "surge", "rally", "drop", "decline",
            "whale", "whales", "institution", "institutional",
            "exchange", "trading", "volume",
        ]
        
        # Check for high-impact keywords
        for keyword in high_impact_keywords:
            if keyword in title_lower:
                return "high"
        
        # Check for medium-impact keywords
        for keyword in medium_impact_keywords:
            if keyword in title_lower:
                return "medium"
        
        # Default to low if no significant keywords found
        return "low"


news_service = NewsService()


