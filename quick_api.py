#!/usr/bin/env python3
"""
Quick API server to serve data from SQLite database
"""
import sqlite3
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = 'backend/gamecalendar.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/health')
def health():
    return {"status": "healthy", "service": "quick-api", "database": "sqlite"}

@app.route('/api/games')
def get_api_games():
    return get_games()

@app.route('/games')
def get_games():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '')
    genre_id = request.args.get('genre_id', type=int)
    platform_id = request.args.get('platform_id', type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    offset = (page - 1) * limit

    conn = get_db_connection()

    # Build query with filters
    where_conditions = []
    params = []

    if search:
        where_conditions.append("name LIKE ?")
        params.append(f"%{search}%")

    if genre_id:
        where_conditions.append("genre_id = ?")
        params.append(genre_id)

    # Platform filtering is not supported - no platform relationship data exists in database
    if platform_id:
        # Skip platform filtering as there's no platform data in the games table
        # Return empty result set to indicate no games match this platform filter
        conn.close()
        return jsonify({
            "games": [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": 0,
                "pages": 0
            }
        })

    # Handle date range filtering (for weeks)
    if start_date and end_date:
        try:
            # Parse date strings to datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Convert to timestamps
            start_timestamp = int(start_dt.timestamp())
            end_timestamp = int(end_dt.timestamp()) + 86399  # Add 23:59:59 to end date
            where_conditions.append("first_release_date >= ? AND first_release_date <= ?")
            params.extend([start_timestamp, end_timestamp])
        except ValueError:
            # Invalid date format, ignore filter
            pass
    elif year and month:
        # Filter by specific month/year
        start_timestamp = int(datetime(year, month, 1).timestamp())
        if month == 12:
            end_timestamp = int(datetime(year + 1, 1, 1).timestamp())
        else:
            end_timestamp = int(datetime(year, month + 1, 1).timestamp())
        where_conditions.append("first_release_date >= ? AND first_release_date < ?")
        params.extend([start_timestamp, end_timestamp])

    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM games {where_clause}"
    total_count = conn.execute(count_query, params).fetchone()['total']

    # Get games
    query = f"""
    SELECT id, igdb_id, name, summary, first_release_date, rating,
           cover_url, total_rating, total_rating_count
    FROM games
    {where_clause}
    ORDER BY first_release_date ASC
    LIMIT ? OFFSET ?
    """

    games = conn.execute(query, params + [limit, offset]).fetchall()

    games_data = []
    for game in games:
        game_dict = dict(game)
        # Convert timestamp to ISO format if exists
        if game_dict['first_release_date']:
            try:
                dt = datetime.fromtimestamp(game_dict['first_release_date'])
                game_dict['first_release_date'] = dt.isoformat()
            except:
                game_dict['first_release_date'] = None
        games_data.append(game_dict)

    conn.close()

    return jsonify({
        "games": games_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    })

@app.route('/api/genres')
def get_api_genres():
    return get_genres()

@app.route('/genres')
def get_genres():
    conn = get_db_connection()
    genres = conn.execute("SELECT * FROM genres ORDER BY name").fetchall()
    conn.close()

    return jsonify([dict(genre) for genre in genres])

@app.route('/api/platforms')
def get_api_platforms():
    return get_platforms()

@app.route('/platforms')
def get_platforms():
    conn = get_db_connection()
    platforms = conn.execute("SELECT * FROM platforms ORDER BY name").fetchall()
    conn.close()

    return jsonify([dict(platform) for platform in platforms])

@app.route('/api/languages')
def get_api_languages():
    return get_languages()

@app.route('/languages')
def get_languages():
    conn = get_db_connection()
    languages = conn.execute("SELECT * FROM languages ORDER BY name").fetchall()
    conn.close()

    return jsonify([dict(language) for language in languages])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)