import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import extract, sql
from sqlalchemy.orm import joinedload
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to the path for relative imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables first
load_dotenv()

# Configure logging with new log_config
from log_config import configure_logging
logger = configure_logging()

# Import app utilities and modules
from utils.route_helpers import log_api_call, FallbackCacheService
from config import Config
from utils.db_utils import get_db, engine
from models import Game, Genre, Platform, Language, Region, Company, Franchise

from services.igdb_service import IGDBService

# Create Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/')
def health_check():
    return {"status": "ok"}

@app.route('/api/genres', methods=['GET'])
@log_api_call
def get_genres():
    try:
        db = next(get_db())
        genres = db.query(Genre).order_by(Genre.name).all()
        
        result = [{
            "id": genre.id,
            "name": genre.name,
            "slug": genre.slug,
            "url": genre.url,
            "created_at": genre.created_at,
            "updated_at": genre.updated_at
        } for genre in genres]
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing genres request")
        return jsonify({'error': str(e)}), 500

@app.route('/api/platforms', methods=['GET'])
@log_api_call
def get_platforms():
    try:
        db = next(get_db())
        platforms = db.query(Platform).order_by(Platform.name).all()
        
        result = [{
            "id": platform.id,
            "name": platform.name,
            "abbreviation": platform.abbreviation,
            "category": platform.category,
            "generation": platform.generation,
            "slug": platform.slug,
            "summary": platform.summary,
            "url": platform.url
        } for platform in platforms]
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing platforms request")
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh-data', methods=['POST'])
@log_api_call
def refresh_data():
    """Endpoint to refresh data from IGDB API"""
    # Check for admin key if provided in header
    admin_mode = request.headers.get('X-Admin-Key') == Config.ADMIN_KEY
    
    try:
        db = next(get_db())
        
        # Determine what data to refresh
        refresh_all = request.args.get('all', 'false').lower() in ('true', '1', 't')
        refresh_games = request.args.get('games', 'false').lower() in ('true', '1', 't') or refresh_all
        refresh_companies = request.args.get('companies', 'false').lower() in ('true', '1', 't')
        
        # Dictionary to track refresh results
        result = {}
        
        # Always refresh essential reference data
        result["genres_updated"] = IGDBService.fetch_genres(db)
        result["platforms_updated"] = IGDBService.fetch_platforms(db)
        result["languages_updated"] = IGDBService.fetch_languages(db)
        result["regions_updated"] = IGDBService.fetch_regions(db)
        # Only fetch companies if explicitly requested
        if refresh_companies:
            logger.info("Companies refresh explicitly requested")
            result["companies_updated"] = IGDBService.fetch_companies(db)
        else:
            result["companies_updated"] = False
            logger.info("Skipping companies refresh - must be explicitly requested")
        result["franchises_updated"] = IGDBService.fetch_franchises(db)
        
        # Refresh games if requested or in admin mode with all=true
        if refresh_games or refresh_all:
            result["games_updated"] = IGDBService.fetch_games_2025(db)
            
            # For current year
            current_year = datetime.now().year
            result[f"games_{current_year}_updated"] = IGDBService.fetch_games_for_year(db, current_year)
            
            # For next year if different from 2025
            if current_year + 1 != 2025:
                result[f"games_{current_year+1}_updated"] = IGDBService.fetch_games_for_year(db, current_year + 1)
        
        return jsonify({
            "success": True,
            "message": "Data refresh completed",
            "details": result
        })
    except Exception as e:
        logger.exception("Error refreshing data")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/languages', methods=['GET'])
@log_api_call
def get_languages():
    try:
        db = next(get_db())
        languages = db.query(Language).order_by(Language.name).all()
        
        result = [{
            "id": lang.id, 
            "name": lang.name,
            "locale": lang.locale, 
            "native_name": lang.native_name,
            "created_at": lang.created_at,
            "updated_at": lang.updated_at
        } for lang in languages]
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing languages request")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regions', methods=['GET'])
@log_api_call
def get_regions():
    try:
        db = next(get_db())
        regions = db.query(Region).order_by(Region.name).all()
        
        result = [{
            "id": region.id, 
            "name": region.name, 
            "identifier": region.identifier,
            "category": region.category,
            "created_at": region.created_at,
            "updated_at": region.updated_at
        } for region in regions]
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing regions request")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/db-status', methods=['GET'])
@log_api_call
def get_db_status():
    if not request.headers.get('X-Admin-Key') == Config.ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        status = {
            "pool_size": engine.pool.size(),
            "checkedin": engine.pool.checkedin(),
            "checkedout": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "status": "healthy"
        }
        
        # Check if we're nearing limits and recycle connections if needed
        if engine.pool.checkedout() > engine.pool.size() * 0.8:
            logger.warning("High connection usage detected, disposing engine connections")
            engine.dispose()
            status["action"] = "connections_recycled"
            
        return jsonify(status)
    except Exception as e:
        logger.exception("Error checking database status")
        return jsonify({'error': str(e)}), 500

@app.route('/api/companies', methods=['GET'])
@log_api_call
def get_companies():
    try:
        db = next(get_db())
        companies = db.query(Company).order_by(Company.name).all()
        
        result = [{
            "id": company.id,
            "name": company.name,
            "slug": company.slug,
            "description": company.description,
            "country": company.country,
            "websites": company.websites,
            "start_date": company.start_date,
            "created_at": company.created_at,
            "updated_at": company.updated_at
        } for company in companies]
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing companies request")
        return jsonify({'error': str(e)}), 500

@app.route('/api/franchises', methods=['GET'])
@log_api_call
def get_franchises():
    try:
        db = next(get_db())
        franchises = db.query(Franchise).order_by(Franchise.name).all()
        
        result = [{
            "id": franchise.id, 
            "name": franchise.name,
            "slug": franchise.slug,
            "url": franchise.url,
            "created_at": franchise.created_at,
            "updated_at": franchise.updated_at
        } for franchise in franchises]
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing franchises request")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/<int:game_id>', methods=['GET'])
@log_api_call
def get_game_details(game_id):
    try:
        db = next(get_db())
        game = db.query(Game).options(
            joinedload(Game.developer),
            joinedload(Game.franchise),
            joinedload(Game.genre),
            joinedload(Game.language)
        ).filter(Game.id == game_id).first()
        
        if not game:
            return jsonify({"error": "Game not found"}), 404
        
        result = {
            "id": game.id,
            "name": game.name,
            "slug": game.slug,
            "summary": game.summary,
            "storyline": game.storyline,
            "release_date": game.release_date.isoformat() if game.release_date else None,
            "rating": game.rating,
            "rating_count": game.rating_count,
            "aggregated_rating": game.aggregated_rating,
            "aggregated_rating_count": game.aggregated_rating_count,
            "total_rating": game.total_rating,
            "total_rating_count": game.total_rating_count,
            "cover_url": game.cover_url,
            "status": game.status,
            "category": game.category,
            "first_release_date": game.first_release_date,
            "hypes": game.hypes,
            "follows": game.follows,
            "url": game.url,
            "video_id": game.video_id,
            "game_engines": game.game_engines,
            "alternative_names": game.alternative_names,
            "videos": game.videos,
            "websites": game.websites,
            "keywords": game.keywords,
            "themes": game.themes,
            "player_perspectives": game.player_perspectives,
            "game_modes": game.game_modes,
            "developer": {"id": game.developer.id, "name": game.developer.name} if game.developer else None,
            "franchise": {"id": game.franchise.id, "name": game.franchise.name} if game.franchise else None,
            "genre": {"id": game.genre.id, "name": game.genre.name} if game.genre else None,
            "language": {"id": game.language.id, "name": game.language.name} if game.language else None
        }
        
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Error retrieving game details for ID {game_id}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/games/search', methods=['GET'])
@log_api_call
def search_games():
    try:
        query = request.args.get('q', '')
        if not query or len(query) < 2:
            return jsonify({"error": "Search query must be at least 2 characters"}), 400
        
        db = next(get_db())
        games = db.query(Game).filter(
            Game.name.ilike(f"%{query}%")
        ).order_by(Game.release_date.desc()).limit(20).all()
        
        result = [{
            "id": game.id,
            "name": game.name,
            "release_date": game.release_date.isoformat() if game.release_date else None,
            "cover_url": game.cover_url,
            "developer": {"id": game.developer.id, "name": game.developer.name} if game.developer else None,
            "franchise": {"id": game.franchise.id, "name": game.franchise.name} if game.franchise else None,
            "genre": {"id": game.genre.id, "name": game.genre.name} if game.genre else None
        } for game in games]
        
        return jsonify(result)
    except Exception as e:
        logger.exception("Error processing game search request")
        return jsonify({'error': str(e)}), 500

@app.route('/api/games', methods=['GET'])
@log_api_call
def get_games():
    """
    Unified endpoint to fetch games with various filters
    
    Query parameters:
    - year: Filter by specific year (e.g., 2025)
    - period: 'current_month', 'upcoming', 'year', 'next_year', 'specific_month', 'date_range'
    - month: When period=specific_month, specify the month (1-12)
    - start_date: When period=date_range, specify start date (YYYY-MM-DD)
    - end_date: When period=date_range, specify end date (YYYY-MM-DD)
    - page: Page number for pagination (default: 1)
    - limit: Number of games per page (default: 50, max: 300)  # Changed from 100 to 300
    - sort: Sort order (default: 'release_date_asc')
    - cached_only: If true, only return games marked as cached (default: false)
    """
    try:
        db = next(get_db())
        
        # Parse query parameters
        period = request.args.get('period', '')
        year = request.args.get('year')
        month = request.args.get('month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = max(1, int(request.args.get('page', '1')))
        limit = min(300, max(1, int(request.args.get('limit', '50'))))  # Changed from 100 to 300
        sort = request.args.get('sort', 'release_date_asc')
        cached_only = request.args.get('cached_only', 'false').lower() in ('true', '1', 't')
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Start building the query
        query = (db.query(Game)
                .options(
                    joinedload(Game.developer),
                    joinedload(Game.franchise),
                    joinedload(Game.genre),
                    joinedload(Game.language)
                ))
        
        # Apply different filters based on period or year
        now = datetime.now()
        
        if period == 'current_month':
            # Filter for current month
            start_of_month = datetime(now.year, now.month, 1)
            end_of_month = datetime(now.year + 1, 1, 1) if now.month == 12 else datetime(now.year, now.month + 1, 1)
            query = query.filter(Game.release_date >= start_of_month, Game.release_date < end_of_month)
            
        elif period == 'specific_month' and month and month.isdigit():
            # Filter for specific month in specific year
            try:
                month_num = int(month)
                year_num = int(year) if year and year.isdigit() else now.year
                
                if 1 <= month_num <= 12:
                    start_of_month = datetime(year_num, month_num, 1)
                    # Handle December case
                    if month_num == 12:
                        end_of_month = datetime(year_num + 1, 1, 1)
                    else:
                        end_of_month = datetime(year_num, month_num + 1, 1)
                        
                    query = query.filter(Game.release_date >= start_of_month, Game.release_date < end_of_month)
            except ValueError:
                return jsonify({"error": "Invalid month or year parameter"}), 400
                
        elif period == 'date_range' and start_date:
            # Filter by date range
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                
                if end_date:
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    end = datetime.combine(end.date(), datetime.max.time())  # End of the end date
                else:
                    # If no end_date, just use a single day
                    end = datetime.combine(start.date(), datetime.max.time())  # End of the start date

                query = query.filter(Game.release_date >= start, Game.release_date <= end)
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
            
        elif period == 'upcoming':
            # Filter for games coming up (from today forward)
            query = query.filter(Game.release_date >= now)
            
        elif period == 'year':
            # Filter for current year
            query = query.filter(extract('year', Game.release_date) == now.year)
            
        elif period == 'next_year':
            # Filter for next year
            query = query.filter(extract('year', Game.release_date) == now.year + 1)
            
        elif year:
            # Filter by specific year if provided
            try:
                year = int(year)
                query = query.filter(extract('year', Game.release_date) == year)
            except ValueError:
                return jsonify({"error": "Invalid year parameter"}), 400
        
        # Apply cached filter if requested
        if cached_only:
            try:
                query = query.filter(Game.is_cached == True)
            except Exception as e:
                logger.warning(f"Error filtering by is_cached: {str(e)}")
        
        # Apply sorting
        if sort == 'release_date_desc':
            query = query.order_by(Game.release_date.desc())
        elif sort == 'name_asc':
            query = query.order_by(Game.name.asc())
        elif sort == 'name_desc':
            query = query.order_by(Game.name.desc())
        else:  # Default: release_date_asc
            query = query.order_by(Game.release_date.asc())
        
        # Apply pagination
        total_count = query.count()
        games = query.offset(offset).limit(limit).all()
        
        # Check if we got results - if not, consider fetching from API
        if not games and not period and year and not cached_only:
            try:
                year_int = int(year)
                current_year = now.year
                
                # Only try to fetch from API for current or future years
                if year_int >= current_year:
                    logger.info(f"No games found for year {year_int}, attempting to fetch from API")
                    
                    # Try to fetch from API (this will update the database)
                    api_success = IGDBService.fetch_games_for_year(db, year_int)
                    
                    if api_success:
                        # Retry the database query now that we have data
                        games = (db.query(Game)
                                .options(
                                    joinedload(Game.developer),
                                    joinedload(Game.franchise),
                                    joinedload(Game.genre),
                                    joinedload(Game.language)
                                )
                                .filter(extract('year', Game.release_date) == year_int)
                                .order_by(Game.release_date.asc())
                                .offset(offset)
                                .limit(limit)
                                .all())
                        
                        # Update total count
                        total_count = db.query(Game).filter(extract('year', Game.release_date) == year_int).count()
                        
                        logger.info(f"Successfully fetched {total_count} games for {year_int} from API")
            except Exception as e:
                logger.error(f"Error trying to fetch games from API: {str(e)}")
        
        # Prepare result
        game_list = []
        for game in games:
            game_data = {
                "id": game.id,
                "name": game.name,
                "release_date": game.release_date.isoformat() if game.release_date else None,
                "cover_url": game.cover_url,
                "summary": game.summary,
                "video_id": game.video_id,
                "developer": {"id": game.developer.id, "name": game.developer.name} if game.developer else None,
                "franchise": {"id": game.franchise.id, "name": game.franchise.name} if game.franchise else None,
                "genre": {"id": game.genre.id, "name": game.genre.name} if game.genre else None,
                "language": {"id": game.language.id, "name": game.language.name} if game.language else None
            }
            game_list.append(game_data)
        
        # Return result with pagination information
        return jsonify({
            "games": game_list,
            "pagination": {
                "total": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit  # Ceiling division
            }
        })
    except Exception as e:
        logger.exception("Error processing games request")
        return jsonify({'error': str(e)}), 500

# Keep these endpoints for backward compatibility, but have them use our unified method
@app.route('/api/games/2025', methods=['GET'])
@log_api_call
def get_games_2025():
    """Legacy endpoint for 2025 games - redirects to unified endpoint"""
    request.args = dict(request.args)
    request.args['year'] = '2025'
    return get_games()

@app.route('/api/games/current-month', methods=['GET'])
@log_api_call
def get_games_current_month():
    """Legacy endpoint for current month games - redirects to unified endpoint"""
    request.args = dict(request.args)
    request.args['period'] = 'current_month'
    return get_games()

@app.route('/api/cached-games', methods=['GET'])
@log_api_call
def get_cached_games():
    """Legacy endpoint for cached games - redirects to unified endpoint"""
    request.args = dict(request.args)
    request.args['cached_only'] = 'true'
    if 'year' not in request.args:
        request.args['year'] = '2025'  # Default year for cached games
    return get_games()

if __name__ == "__main__":
    from services.startup_loader import StartupLoader
    StartupLoader.run_flask_app(app)