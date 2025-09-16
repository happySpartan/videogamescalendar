import requests
import logging
import sys
import os
import time
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List, Optional, Tuple, Callable, TypeVar, Union

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
from models import Genre, Game, Language, Region, Company, Franchise, Platform

logger = logging.getLogger(__name__)

# Type variable for generic function return
T = TypeVar('T')

class IGDBService:
    # Base URL for IGDB API
    BASE_API_URL = "https://api.igdb.com/v4"
    
    # Standard page size for pagination - increased from 100 to 300
    PAGE_SIZE = 300
    
    # Delay between API calls to avoid rate limiting
    API_CALL_DELAY = 0.3  # seconds
    
    # Cache for access token to avoid repeatedly fetching it
    _access_token = None
    _token_expires_at = None
    
    @classmethod
    def get_access_token(cls) -> Optional[str]:
        """Get Twitch/IGDB access token with caching"""
        # Check if we have a valid cached token
        now = datetime.utcnow()
        if cls._access_token and cls._token_expires_at and now < cls._token_expires_at:
            return cls._access_token
            
        try:
            auth_url = "https://id.twitch.tv/oauth2/token"
            auth_params = {
                "client_id": Config.TWITCH_CLIENT_ID,
                "client_secret": Config.TWITCH_CLIENT_SECRET,
                "grant_type": "client_credentials"
            }
            
            logger.info("Requesting new access token from Twitch API")
            response = requests.post(auth_url, params=auth_params)
            
            if response.status_code == 200:
                data = response.json()
                cls._access_token = data["access_token"]
                # Set expiry time slightly before actual expiry to be safe
                expires_in = data.get("expires_in", 14400)  # Default 4 hours
                cls._token_expires_at = now + timedelta(seconds=expires_in - 300)  # 5 minutes safety margin
                logger.info(f"Received new access token, valid until {cls._token_expires_at}")
                return cls._access_token
            else:
                logger.error(f"Failed to get access token. Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None
    
    @classmethod
    def get_auth_headers(cls) -> Optional[Dict[str, str]]:
        """Get authentication headers for IGDB API"""
        access_token = cls.get_access_token()
        if not access_token:
            return None
            
        return {
            "Client-ID": Config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }
    
    @classmethod
    def make_api_request(
        cls,
        endpoint: str, 
        query_body: str, 
        max_retries: int = 3
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Make a request to the IGDB API with retry logic and error handling
        
        Args:
            endpoint: API endpoint path (e.g., 'games', 'platforms')
            query_body: IGDB query syntax
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (success, data)
        """
        headers = cls.get_auth_headers()
        if not headers:
            logger.error("Failed to get authentication headers")
            return False, []
            
        url = f"{cls.BASE_API_URL}/{endpoint}"
        logger.debug(f"Making API request to {url} with query: {query_body}")
        
        retries = 0
        while retries < max_retries:
            try:
                response = requests.post(url, headers=headers, data=query_body)
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.debug(f"Received {len(data)} items from {endpoint}")
                        return True, data
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON response from {endpoint}: {response.text[:200]}")
                        return False, []
                elif response.status_code == 401:
                    logger.error(f"Authentication error: {response.text}")
                    # Force token refresh on next attempt
                    cls._access_token = None
                    retries += 1
                    continue
                elif response.status_code == 429:
                    # Rate limiting - wait longer before retrying
                    wait_time = 2 ** retries  # Exponential backoff
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry. Response: {response.text}")
                    time.sleep(wait_time)
                    retries += 1
                    continue
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    retries += 1
                    time.sleep(cls.API_CALL_DELAY)
            except requests.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                retries += 1
                time.sleep(cls.API_CALL_DELAY)
                
        logger.error(f"Failed to fetch data from {endpoint} after {max_retries} retries")
        return False, []
    
    @classmethod
    def paginate_api_requests(
        cls,
        endpoint: str,
        fields: str,
        where_clause: str = "",
        sort_clause: str = "",
        process_func: Callable[[Session, List[Dict[str, Any]]], int] = None,
        db: Session = None
    ) -> Tuple[bool, int]:
        """Paginate through API results using offset and limit
        
        Args:
            endpoint: API endpoint path
            fields: Fields to request
            where_clause: Optional where clause
            sort_clause: Optional sort clause
            process_func: Function to process each page of results
            db: Database session for processing
            
        Returns:
            Tuple of (success, count)
        """
        offset = 0
        total_processed = 0
        more_available = True
        
        while more_available:
            # Build query with pagination - FIX: Ensure proper formatting of query string
            query = f"{fields}"
            
            if where_clause and where_clause.strip():
                query += f" {where_clause.strip()}"
                
            if sort_clause and sort_clause.strip():
                query += f" {sort_clause.strip()}"
                
            # Add explicit limit and offset with proper formatting
            query += f" limit {cls.PAGE_SIZE}; offset {offset};"
            
            # Log the complete query string for debugging
            logger.debug(f"API Query: {query}")
            
            success, data = cls.make_api_request(endpoint, query)
            
            if not success:
                logger.error(f"API request failed for {endpoint} with offset {offset}")
                return False, total_processed
                
            batch_count = len(data)
            logger.info(f"Fetched {batch_count} {endpoint} (offset: {offset})")
            
            if batch_count == 0:
                more_available = False
                break
                
            # Process the batch if a processing function is provided
            if process_func and db:
                try:
                    items_added = process_func(db, data)
                    total_processed += items_added
                    db.commit()
                    logger.info(f"Processed {items_added} {endpoint} (total: {total_processed})")
                except SQLAlchemyError as e:
                    logger.error(f"Database error processing {endpoint} data: {str(e)}")
                    db.rollback()
                    # Continue to next batch despite error
                except Exception as e:
                    logger.error(f"Error processing {endpoint} data: {str(e)}")
                    db.rollback()
                    # Continue to next batch despite error
            
            # Update offset for next batch
            offset += batch_count
            
            # If we got fewer items than the page size, we've reached the end
            if batch_count < cls.PAGE_SIZE:
                more_available = False
            
            # Small delay to avoid rate limiting
            time.sleep(cls.API_CALL_DELAY)
        
        return True, total_processed
    
    @staticmethod
    def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get a value from a dictionary"""
        if isinstance(data, dict) and key in data:
            return data[key]
        return default
    
    @staticmethod
    def process_genres(db: Session, genres_data: List[Dict[str, Any]]) -> int:
        """Process genre data and store in database"""
        now = datetime.utcnow()
        now_timestamp = int(now.timestamp())
        genres_added = 0
        genres_updated = 0
        
        for genre_data in genres_data:
            # Skip records without required fields
            if not genre_data.get("id"):
                logger.warning(f"Skipping genre record missing ID: {genre_data}")
                continue
                
            # Check if genre already exists by IGDB ID
            existing = db.query(Genre).filter_by(igdb_id=genre_data.get("id")).first()
            
            if existing:
                # Update existing genre
                existing.name = genre_data.get("name", existing.name or "Unknown")
                existing.slug = genre_data.get("slug", existing.slug)
                existing.url = genre_data.get("url", existing.url)
                existing.created_at = genre_data.get("created_at", existing.created_at)
                existing.updated_at = genre_data.get("updated_at", existing.updated_at)
                existing.downloaded_at = now
                existing.checksum = genre_data.get("checksum", existing.checksum)
                genres_updated += 1
            else:
                # Create new genre
                try:
                    genre = Genre(
                        igdb_id=genre_data.get("id"),
                        name=genre_data.get("name", "Unknown"),
                        slug=genre_data.get("slug"),
                        url=genre_data.get("url"),
                        created_at=genre_data.get("created_at", now_timestamp),
                        updated_at=genre_data.get("updated_at", now_timestamp),
                        downloaded_at=now,
                        checksum=genre_data.get("checksum")
                    )
                    db.add(genre)
                    genres_added += 1
                except Exception as e:
                    logger.error(f"Error adding genre {genre_data.get('name')}: {str(e)}")
        
        logger.info(f"Genres: {genres_added} added, {genres_updated} updated")
        return genres_added + genres_updated

    @staticmethod
    def fetch_genres(db: Session) -> bool:
        """Fetch genres from IGDB API and store in database"""
        logger.info("Fetching genres from IGDB API")
        
        fields = "fields id, name, slug, url, created_at, updated_at, checksum;"
        sort = "sort name asc;"
        
        success, count = IGDBService.paginate_api_requests(
            endpoint="genres",
            fields=fields,
            sort_clause=sort,
            process_func=IGDBService.process_genres,
            db=db
        )
        
        if success:
            logger.info(f"Successfully fetched and processed {count} genres")
            return True
        else:
            logger.error("Failed to fetch genres")
            return False

    @staticmethod
    def process_platforms(db: Session, platforms_data: List[Dict[str, Any]]) -> int:
        """Process platform data and store in database"""
        now = datetime.utcnow()
        now_timestamp = int(now.timestamp())
        platforms_added = 0
        platforms_updated = 0
        
        for platform_data in platforms_data:
            # Skip records without required fields
            if not platform_data.get("id"):
                logger.warning(f"Skipping platform record missing ID: {platform_data}")
                continue
                
            # Check if platform already exists by IGDB ID
            existing = db.query(Platform).filter_by(igdb_id=platform_data.get("id")).first()
            
            if existing:
                # Update existing platform
                existing.name = platform_data.get("name", existing.name)
                existing.abbreviation = platform_data.get("abbreviation", existing.abbreviation)
                # Removed alternative_name field
                existing.category = platform_data.get("category", existing.category)
                existing.generation = platform_data.get("generation", existing.generation)
                existing.slug = platform_data.get("slug", existing.slug)
                existing.summary = platform_data.get("summary", existing.summary)
                existing.url = platform_data.get("url", existing.url)
                existing.created_at = platform_data.get("created_at", existing.created_at)
                existing.updated_at = platform_data.get("updated_at", existing.updated_at)
                existing.downloaded_at = now
                existing.checksum = platform_data.get("checksum", existing.checksum)
                platforms_updated += 1
            else:
                # Create new platform
                try:
                    platform = Platform(
                        igdb_id=platform_data.get("id"),
                        name=platform_data.get("name", "Unknown"),
                        abbreviation=platform_data.get("abbreviation"),
                        # Removed alternative_name field
                        category=platform_data.get("category"),
                        generation=platform_data.get("generation"),
                        slug=platform_data.get("slug"),
                        summary=platform_data.get("summary"),
                        url=platform_data.get("url"),
                        created_at=platform_data.get("created_at", now_timestamp),
                        updated_at=platform_data.get("updated_at", now_timestamp),
                        downloaded_at=now,
                        checksum=platform_data.get("checksum")
                    )
                    db.add(platform)
                    platforms_added += 1
                except Exception as e:
                    logger.error(f"Error adding platform {platform_data.get('name')}: {str(e)}")
        
        logger.info(f"Platforms: {platforms_added} added, {platforms_updated} updated")
        return platforms_added + platforms_updated
    
    @staticmethod
    def fetch_platforms(db: Session) -> bool:
        """Fetch platforms from IGDB API and store in database"""
        logger.info("Fetching platforms from IGDB API")
        
        fields = """
            fields id, name, abbreviation, category, 
                   generation, slug, summary, url, created_at, updated_at, checksum;
        """
        sort = "sort name asc;"
        
        success, count = IGDBService.paginate_api_requests(
            endpoint="platforms",
            fields=fields,
            sort_clause=sort,
            process_func=IGDBService.process_platforms,
            db=db
        )
        
        if success:
            logger.info(f"Successfully fetched and processed {count} platforms")
            return True
        else:
            logger.error("Failed to fetch platforms")
            return False
    
    @staticmethod
    def process_languages(db: Session, languages_data: List[Dict[str, Any]]) -> int:
        """Process language data and store in database"""
        now_timestamp = int(datetime.utcnow().timestamp())
        languages_added = 0
        
        for language_data in languages_data:
            # Check if language already exists by IGDB ID
            existing = db.query(Language).filter_by(igdb_id=language_data.get("id")).first()
            
            if existing:
                # Update existing language
                existing.name = language_data.get("name", existing.name)
                existing.native_name = language_data.get("native_name", existing.native_name)
                existing.locale = language_data.get("locale", existing.locale)
                existing.created_at = language_data.get("created_at", existing.created_at)
                existing.updated_at = language_data.get("updated_at", existing.updated_at)
                existing.downloaded_at = datetime.utcnow()
                existing.checksum = language_data.get("checksum", existing.checksum)
            else:
                # Create new language
                language = Language(
                    igdb_id=language_data.get("id"),
                    name=language_data.get("name", "Unknown"),
                    native_name=language_data.get("native_name"),
                    locale=language_data.get("locale"),
                    created_at=language_data.get("created_at", now_timestamp),
                    updated_at=language_data.get("updated_at", now_timestamp),
                    downloaded_at=datetime.utcnow(),
                    checksum=language_data.get("checksum")
                )
                db.add(language)
                languages_added += 1
        
        return languages_added
    
    @staticmethod
    def fetch_languages(db: Session) -> bool:
        """Fetch languages from IGDB API and store in database"""
        logger.info("Fetching languages from IGDB API")
        
        fields = "fields id, name, native_name, locale, created_at, updated_at, checksum;"
        sort = "sort name asc;"
        
        success, count = IGDBService.paginate_api_requests(
            endpoint="languages",
            fields=fields,
            sort_clause=sort,
            process_func=IGDBService.process_languages,
            db=db
        )
        
        if success:
            logger.info(f"Successfully fetched and processed {count} languages")
            return True
        else:
            logger.error("Failed to fetch languages")
            return False
    
    @staticmethod
    def process_regions(db: Session, regions_data: List[Dict[str, Any]]) -> int:
        """Process region data and store in database"""
        now_timestamp = int(datetime.utcnow().timestamp())
        regions_added = 0
        
        for region_data in regions_data:
            # Check if region already exists by IGDB ID
            existing = db.query(Region).filter_by(igdb_id=region_data.get("id")).first()
            
            if existing:
                # Update existing region
                existing.name = region_data.get("name", existing.name)
                existing.category = region_data.get("category", existing.category)
                existing.identifier = region_data.get("identifier", existing.identifier)
                existing.created_at = region_data.get("created_at", existing.created_at)
                existing.updated_at = region_data.get("updated_at", existing.updated_at)
                existing.downloaded_at = datetime.utcnow()
                existing.checksum = region_data.get("checksum", existing.checksum)
            else:
                # Create new region
                region = Region(
                    igdb_id=region_data.get("id"),
                    name=region_data.get("name", "Unknown"),
                    category=region_data.get("category"),
                    identifier=region_data.get("identifier"),
                    created_at=region_data.get("created_at", now_timestamp),
                    updated_at=region_data.get("updated_at", now_timestamp),
                    downloaded_at=datetime.utcnow(),
                    checksum=region_data.get("checksum")
                )
                db.add(region)
                regions_added += 1
        
        return regions_added
    
    @staticmethod
    def fetch_regions(db: Session) -> bool:
        """Fetch regions from IGDB API and store in database"""
        logger.info("Fetching regions from IGDB API")
        
        fields = "fields id, name, category, identifier, created_at, updated_at, checksum;"
        sort = "sort name asc;"
        
        success, count = IGDBService.paginate_api_requests(
            endpoint="regions",
            fields=fields,
            sort_clause=sort,
            process_func=IGDBService.process_regions,
            db=db
        )
        
        if success:
            logger.info(f"Successfully fetched and processed {count} regions")
            return True
        else:
            logger.error("Failed to fetch regions")
            return False
    
    @staticmethod
    def process_companies(db: Session, companies_data: List[Dict[str, Any]]) -> int:
        """Process company data and store in database"""
        now = datetime.utcnow()
        now_timestamp = int(now.timestamp())
        companies_added = 0
        companies_updated = 0
        
        for company_data in companies_data:
            # Skip records without required fields
            if not company_data.get("id"):
                logger.warning(f"Skipping company record missing ID: {company_data}")
                continue
                
            # Check if company already exists by IGDB ID
            existing = db.query(Company).filter_by(igdb_id=company_data.get("id")).first()
            
            # Handle websites data which is an array in IGDB
            websites_json = None
            if "websites" in company_data and company_data["websites"]:
                try:
                    websites_json = json.dumps(company_data["websites"])
                except:
                    websites_json = str(company_data["websites"])
            
            if existing:
                # Update existing company
                existing.name = company_data.get("name", existing.name)
                existing.slug = company_data.get("slug", existing.slug)
                existing.description = company_data.get("description", existing.description)
                existing.country = company_data.get("country", existing.country)
                existing.websites = websites_json  # Changed from website to websites (JSON array)
                existing.start_date = company_data.get("start_date", existing.start_date)
                existing.created_at = company_data.get("created_at", existing.created_at)
                existing.updated_at = company_data.get("updated_at", existing.updated_at)
                existing.downloaded_at = now
                existing.checksum = company_data.get("checksum", existing.checksum)
                companies_updated += 1
            else:
                # Create new company
                try:
                    company = Company(
                        igdb_id=company_data.get("id"),
                        name=company_data.get("name", "Unknown"),
                        slug=company_data.get("slug"),
                        description=company_data.get("description"),
                        country=company_data.get("country"),
                        websites=websites_json,  # Changed from website to websites (JSON array)
                        start_date=company_data.get("start_date"),
                        created_at=company_data.get("created_at", now_timestamp),
                        updated_at=company_data.get("updated_at", now_timestamp),
                        downloaded_at=now,
                        checksum=company_data.get("checksum")
                    )
                    db.add(company)
                    companies_added += 1
                except Exception as e:
                    logger.error(f"Error adding company {company_data.get('name')}: {str(e)}")
        
        logger.info(f"Companies: {companies_added} added, {companies_updated} updated")
        return companies_added + companies_updated
    
    @staticmethod
    def fetch_companies(db: Session) -> bool:
        """Fetch companies from IGDB API and store in database"""
        logger.info("Fetching companies from IGDB API")
        
        fields = """
            fields id, name, slug, description, country, websites,  
                   start_date, created_at, updated_at, checksum;
        """  # Changed 'website' to 'websites' in the query
        sort = "sort name asc;"
        
        success, count = IGDBService.paginate_api_requests(
            endpoint="companies",
            fields=fields,
            sort_clause=sort,
            process_func=IGDBService.process_companies,
            db=db
        )
        
        if success:
            logger.info(f"Successfully fetched and processed {count} companies")
            return True
        else:
            logger.error("Failed to fetch companies")
            return False
    
    @staticmethod
    def process_franchises(db: Session, franchises_data: List[Dict[str, Any]]) -> int:
        """Process franchise data and store in database"""
        now_timestamp = int(datetime.utcnow().timestamp())
        franchises_added = 0
        franchises_updated = 0  # Add a counter for updates
        
        for franchise_data in franchises_data:
            # Check if franchise already exists by IGDB ID
            existing = db.query(Franchise).filter_by(igdb_id=franchise_data.get("id")).first()
            
            if existing:
                # Update existing franchise
                existing.name = franchise_data.get("name", existing.name)
                existing.slug = franchise_data.get("slug", existing.slug)
                existing.url = franchise_data.get("url", existing.url)
                existing.created_at = franchise_data.get("created_at", existing.created_at)
                existing.updated_at = franchise_data.get("updated_at", existing.updated_at)
                existing.downloaded_at = datetime.utcnow()
                existing.checksum = franchise_data.get("checksum", existing.checksum)
                franchises_updated += 1  # Increment the counter for updates
            else:
                # Create new franchise
                franchise = Franchise(
                    igdb_id=franchise_data.get("id"),
                    name=franchise_data.get("name", "Unknown"),
                    slug=franchise_data.get("slug"),
                    url=franchise_data.get("url"),
                    created_at=franchise_data.get("created_at", now_timestamp),
                    updated_at=franchise_data.get("updated_at", now_timestamp),
                    downloaded_at=datetime.utcnow(),
                    checksum=franchise_data.get("checksum")
                )
                db.add(franchise)
                franchises_added += 1
        
        logger.info(f"Franchises: {franchises_added} added, {franchises_updated} updated")
        return franchises_added + franchises_updated  # Return the total count of processed records
    
    @staticmethod
    def fetch_franchises(db: Session) -> bool:
        """Fetch franchises from IGDB API and store in database"""
        logger.info("Fetching franchises from IGDB API")
        
        fields = "fields id, name, slug, url, created_at, updated_at, checksum;"
        sort = "sort name asc;"
        
        success, count = IGDBService.paginate_api_requests(
            endpoint="franchises",
            fields=fields,
            sort_clause=sort,
            process_func=IGDBService.process_franchises,
            db=db
        )
        
        if success:
            logger.info(f"Successfully fetched and processed {count} franchises")
            return True
        else:
            logger.error("Failed to fetch franchises")
            return False
    
    @staticmethod
    def process_games(db: Session, games_data: List[Dict[str, Any]]) -> int:
        """Process game data and store in database"""
        now = datetime.utcnow()
        now_timestamp = int(now.timestamp())
        games_added = 0
        games_updated = 0
        
        for game_data in games_data:
            try:
                # Skip records without required fields
                if not game_data.get("id"):
                    logger.warning(f"Skipping game record missing ID")
                    continue
                    
                # Check if game already exists by IGDB ID
                existing = db.query(Game).filter_by(igdb_id=game_data.get("id")).first()
                
                # Extract cover URL if available
                cover_url = None
                if "cover" in game_data and isinstance(game_data["cover"], dict) and "url" in game_data["cover"]:
                    cover_url = game_data["cover"]["url"]
                    if cover_url and not cover_url.startswith(('http://', 'https://')):
                        cover_url = f"https:{cover_url}"
                
                # Get primary video ID if available
                video_id = None
                if "videos" in game_data and game_data["videos"]:
                    for video in game_data["videos"]:
                        if isinstance(video, dict) and "video_id" in video:
                            video_id = video["video_id"]
                            break
                
                # Get release date as datetime
                release_date = None
                if "first_release_date" in game_data and game_data["first_release_date"]:
                    try:
                        release_date = datetime.fromtimestamp(game_data["first_release_date"])
                    except Exception as e:
                        logger.warning(f"Invalid release date for game {game_data.get('name')}: {e}")
                
                # Process related entities
                developer_id = IGDBService._process_developer(db, game_data)
                franchise_id = IGDBService._process_franchise(db, game_data)
                genre_id = IGDBService._process_genre(db, game_data)
                language_id = IGDBService._process_language(db, game_data)
                
                # Process JSON fields
                alt_names_json = IGDBService._serialize_field(game_data, "alternative_names")
                videos_json = IGDBService._serialize_field(game_data, "videos")
                websites_json = IGDBService._serialize_field(game_data, "websites")
                keywords_json = IGDBService._serialize_field(game_data, "keywords")
                themes_json = IGDBService._serialize_field(game_data, "themes")
                perspectives_json = IGDBService._serialize_field(game_data, "player_perspectives")
                game_modes_json = IGDBService._serialize_field(game_data, "game_modes")
                
                # Extract game engine names
                game_engines = None
                if "game_engines" in game_data and game_data["game_engines"]:
                    engine_names = []
                    for engine in game_data["game_engines"]:
                        if isinstance(engine, dict) and "name" in engine:
                            engine_names.append(engine["name"])
                    game_engines = ", ".join(engine_names) if engine_names else None
                
                if existing:
                    # Update existing game
                    existing.name = game_data.get("name", existing.name or "Unknown Game")
                    existing.slug = game_data.get("slug", existing.slug)
                    existing.summary = game_data.get("summary", existing.summary)
                    existing.storyline = game_data.get("storyline", existing.storyline)
                    existing.release_date = release_date or existing.release_date
                    existing.rating = game_data.get("rating", existing.rating)
                    existing.rating_count = game_data.get("rating_count", existing.rating_count)
                    existing.aggregated_rating = game_data.get("aggregated_rating", existing.aggregated_rating)
                    existing.aggregated_rating_count = game_data.get("aggregated_rating_count", existing.aggregated_rating_count)
                    existing.total_rating = game_data.get("total_rating", existing.total_rating)
                    existing.total_rating_count = game_data.get("total_rating_count", existing.total_rating_count)
                    if cover_url:  # Only update if we have a new value
                        existing.cover_url = cover_url
                    existing.status = game_data.get("status", existing.status)
                    existing.category = game_data.get("category", existing.category)
                    existing.first_release_date = game_data.get("first_release_date", existing.first_release_date)
                    existing.hypes = game_data.get("hypes", existing.hypes)
                    existing.follows = game_data.get("follows", existing.follows)
                    existing.url = game_data.get("url", existing.url)
                    existing.game_engines = game_engines or existing.game_engines
                    existing.alternative_names = alt_names_json or existing.alternative_names
                    existing.videos = videos_json or existing.videos
                    existing.websites = websites_json or existing.websites
                    existing.keywords = keywords_json or existing.keywords
                    existing.themes = themes_json or existing.themes
                    existing.player_perspectives = perspectives_json or existing.player_perspectives
                    existing.game_modes = game_modes_json or existing.game_modes
                    existing.video_id = video_id or existing.video_id
                    if developer_id:
                        existing.developer_id = developer_id
                    if franchise_id:
                        existing.franchise_id = franchise_id
                    if genre_id:
                        existing.genre_id = genre_id
                    if language_id:
                        existing.language_id = language_id
                    existing.created_at = game_data.get("created_at", existing.created_at)
                    existing.updated_at = game_data.get("updated_at", existing.updated_at)
                    existing.downloaded_at = now
                    existing.checksum = game_data.get("checksum", existing.checksum)
                    games_updated += 1
                else:
                    # Create new game
                    game = Game(
                        igdb_id=game_data.get("id"),
                        name=game_data.get("name", "Unknown Game"),
                        slug=game_data.get("slug"),
                        summary=game_data.get("summary"),
                        storyline=game_data.get("storyline"),
                        release_date=release_date,
                        rating=game_data.get("rating"),
                        rating_count=game_data.get("rating_count"),
                        aggregated_rating=game_data.get("aggregated_rating"),
                        aggregated_rating_count=game_data.get("aggregated_rating_count"),
                        total_rating=game_data.get("total_rating"),
                        total_rating_count=game_data.get("total_rating_count"),
                        cover_url=cover_url,
                        status=game_data.get("status"),
                        category=game_data.get("category"),
                        first_release_date=game_data.get("first_release_date"),
                        hypes=game_data.get("hypes"),
                        follows=game_data.get("follows"),
                        url=game_data.get("url"),
                        game_engines=game_engines,
                        alternative_names=alt_names_json,
                        videos=videos_json,
                        websites=websites_json,
                        keywords=keywords_json,
                        themes=themes_json,
                        player_perspectives=perspectives_json,
                        game_modes=game_modes_json,
                        video_id=video_id,
                        developer_id=developer_id,
                        franchise_id=franchise_id,
                        genre_id=genre_id,
                        language_id=language_id,
                        created_at=game_data.get("created_at", now_timestamp),
                        updated_at=game_data.get("updated_at", now_timestamp),
                        downloaded_at=now,
                        checksum=game_data.get("checksum")
                    )
                    db.add(game)
                    games_added += 1
            except Exception as e:
                logger.error(f"Error processing game {game_data.get('name', '(unknown)')}: {str(e)}")
                # Continue processing other games despite this error
        
        logger.info(f"Games: {games_added} added, {games_updated} updated")
        return games_added + games_updated
    
    @staticmethod
    def _process_developer(db: Session, game_data: Dict[str, Any]) -> Optional[int]:
        """Extract and process developer information"""
        if "involved_companies" not in game_data or not game_data["involved_companies"]:
            return None
            
        try:
            for involved in game_data["involved_companies"]:
                if not isinstance(involved, dict):
                    continue
                    
                if involved.get("developer", False):
                    developer_data = involved.get("company", {})
                    if not developer_data or not developer_data.get("id"):
                        continue
                        
                    developer = db.query(Company).filter_by(igdb_id=developer_data.get("id")).first()
                    
                    # If developer doesn't exist, create it
                    if not developer:
                        developer = Company(
                            igdb_id=developer_data.get("id"),
                            name=developer_data.get("name", "Unknown Developer"),
                            slug=developer_data.get("slug"),
                            description=developer_data.get("description"),
                            country=developer_data.get("country"),
                            website=developer_data.get("website"),
                            downloaded_at=datetime.utcnow()
                        )
                        db.add(developer)
                        db.flush()  # Generate ID but don't commit yet
                    
                    if developer:
                        return developer.id
        except Exception as e:
            logger.warning(f"Error processing developer: {str(e)}")
            
        return None
    
    @staticmethod
    def _process_franchise(db: Session, game_data: Dict[str, Any]) -> Optional[int]:
        """Extract and process franchise information"""
        if "franchise" not in game_data or not game_data["franchise"]:
            return None
            
        try:
            franchise_data = game_data["franchise"]
            if not isinstance(franchise_data, dict) or not franchise_data.get("id"):
                return None
                
            franchise = db.query(Franchise).filter_by(igdb_id=franchise_data.get("id")).first()
            
            # If franchise doesn't exist, create it
            if not franchise:
                franchise = Franchise(
                    igdb_id=franchise_data.get("id"),
                    name=franchise_data.get("name", "Unknown Franchise"),
                    slug=franchise_data.get("slug"),
                    url=franchise_data.get("url"),
                    downloaded_at=datetime.utcnow()
                )
                db.add(franchise)
                db.flush()  # Generate ID but don't commit yet
            
            if franchise:
                return franchise.id
        except Exception as e:
            logger.warning(f"Error processing franchise: {str(e)}")
            
        return None
    
    @staticmethod
    def _process_genre(db: Session, game_data: Dict[str, Any]) -> Optional[int]:
        """Extract and process genre information"""
        if "genres" not in game_data or not game_data["genres"]:
            return None
            
        try:
            genres = game_data["genres"]
            if not genres or not isinstance(genres, list) or not genres[0]:
                return None
                
            genre_data = genres[0]  # Take first genre
            if not isinstance(genre_data, dict) or not genre_data.get("id"):
                return None
                
            genre = db.query(Genre).filter_by(igdb_id=genre_data.get("id")).first()
            
            # If genre doesn't exist, create it
            if not genre:
                genre = Genre(
                    igdb_id=genre_data.get("id"),
                    name=genre_data.get("name", "Unknown Genre"),
                    slug=genre_data.get("slug"),
                    url=genre_data.get("url"),
                    downloaded_at=datetime.utcnow()
                )
                db.add(genre)
                db.flush()  # Generate ID but don't commit yet
            
            if genre:
                return genre.id
        except Exception as e:
            logger.warning(f"Error processing genre: {str(e)}")
            
        return None
    
    @staticmethod
    def _process_language(db: Session, game_data: Dict[str, Any]) -> Optional[int]:
        """Extract and process language information"""
        if "language_supports" not in game_data or not game_data["language_supports"]:
            return None
            
        try:
            for lang_support in game_data["language_supports"]:
                if not isinstance(lang_support, dict) or "language" not in lang_support:
                    continue
                    
                lang_data = lang_support["language"]
                if not isinstance(lang_data, dict) or not lang_data.get("id"):
                    continue
                    
                language = db.query(Language).filter_by(igdb_id=lang_data.get("id")).first()
                
                if language:
                    return language.id
        except Exception as e:
            logger.warning(f"Error processing language: {str(e)}")
            
        return None
    
    @staticmethod
    def _serialize_field(game_data: Dict[str, Any], field_name: str) -> Optional[str]:
        """Safely serialize a field to JSON"""
        if field_name not in game_data or not game_data[field_name]:
            return None
            
        try:
            return json.dumps(game_data[field_name])
        except Exception:
            return str(game_data[field_name])
    
    @classmethod
    def fetch_games_for_year(cls, db: Session, year: int) -> bool:
        """Fetch games releasing in a specific year from IGDB API and store in database"""
        logger.info(f"Fetching games for {year} from IGDB API")
        
        # Calculate timestamps for the year
        start_timestamp = int(datetime(year, 1, 1).timestamp())
        end_timestamp = int(datetime(year, 12, 31, 23, 59, 59).timestamp())
        
        # Ensure we have required reference data first
        logger.info("Ensuring required reference data is available...")
        # MODIFIED: Skip companies fetch when loading games
        # cls.fetch_companies(db)
        cls.fetch_franchises(db)
        cls.fetch_genres(db)
        cls.fetch_languages(db)
        
        # Now fetch games
        fields = """
            fields id, name, slug, summary, storyline, first_release_date, rating, 
                   rating_count, aggregated_rating, aggregated_rating_count, 
                   total_rating, total_rating_count, cover.url, status, category,
                   hypes, follows, url, game_engines.name, alternative_names,
                   videos.video_id, websites, keywords, themes, player_perspectives,
                   game_modes, involved_companies.company.*, involved_companies.developer,
                   franchise.*, genres.*, language_supports.language.*,
                   created_at, updated_at, checksum;
        """
        where = f"where first_release_date >= {start_timestamp} & first_release_date <= {end_timestamp};"
        sort = "sort first_release_date asc;"
        
        success, count = cls.paginate_api_requests(
            endpoint="games",
            fields=fields,
            where_clause=where,
            sort_clause=sort,
            process_func=cls.process_games,
            db=db
        )
        
        if success:
            logger.info(f"Successfully fetched and processed {count} games for {year}")
            return True
        else:
            logger.error(f"Failed to fetch games for {year}")
            return False
    
    @classmethod
    def fetch_games_2025(cls, db: Session) -> bool:
        """Fetch games releasing in 2025 from IGDB API and store in database"""
        return cls.fetch_games_for_year(db, 2025)