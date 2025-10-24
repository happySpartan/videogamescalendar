#!/usr/bin/env python3
"""
Simple database viewer for the game calendar SQLite database
"""
import sqlite3
from datetime import datetime

DB_PATH = 'backend/gamecalendar.db'

def format_timestamp(timestamp):
    if timestamp:
        try:
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            return str(timestamp)
    return 'N/A'

def show_database_stats():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("=== VIDEO GAME CALENDAR DATABASE ===\n")

    # Show table counts
    tables = ['games', 'genres', 'platforms', 'languages', 'regions', 'companies', 'franchises']
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table.capitalize():<12}: {count:>6}")

    print("\n=== TOP 10 HIGHEST RATED GAMES ===")
    games = conn.execute("""
        SELECT name, rating, total_rating_count, first_release_date
        FROM games
        WHERE rating IS NOT NULL AND total_rating_count > 10
        ORDER BY rating DESC
        LIMIT 10
    """).fetchall()

    for i, game in enumerate(games, 1):
        release_date = format_timestamp(game['first_release_date'])
        print(f"{i:2}. {game['name']:<40} | Rating: {game['rating']:5.1f} | Release: {release_date}")

    print("\n=== UPCOMING GAMES (2025) ===")
    upcoming = conn.execute("""
        SELECT name, first_release_date, total_rating_count
        FROM games
        WHERE first_release_date > strftime('%s', '2025-01-01')
        AND first_release_date < strftime('%s', '2026-01-01')
        ORDER BY first_release_date ASC
        LIMIT 10
    """).fetchall()

    for game in upcoming:
        release_date = format_timestamp(game['first_release_date'])
        print(f"• {game['name']:<40} | Release: {release_date}")

    print(f"\n=== RANDOM SAMPLE GAMES ===")
    sample = conn.execute("""
        SELECT name, summary, first_release_date
        FROM games
        WHERE summary IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 5
    """).fetchall()

    for game in sample:
        release_date = format_timestamp(game['first_release_date'])
        summary = game['summary'][:100] + "..." if len(game['summary']) > 100 else game['summary']
        print(f"\n📦 {game['name']} ({release_date})")
        print(f"   {summary}")

    conn.close()

if __name__ == '__main__':
    show_database_stats()