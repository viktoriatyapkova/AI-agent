from typing import Dict, List
from langchain.tools import tool
from database import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

@tool
def get_book_recommendations(genre: str = None, age_limit: str = None, 
                           author_origin: str = None, keywords: List[str] = None) -> List[Dict]:
    """Возвращает рекомендации книг с обработкой кодировки"""
    conn = get_connection()
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    
    if genre:
        query += " AND genre = %s"
        params.append(genre)
    if age_limit:
        query += " AND age_limit <= %s"
        params.append(age_limit)
    if author_origin:
        query += " AND author_origin = %s"
        params.append(author_origin)
    if keywords:
        query += " AND keywords @> %s"
        params.append(keywords)
    
    query += " ORDER BY rating DESC LIMIT 5;"
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

        books = []
        for row in rows:
            book = {}
            for key, value in row.items():
                if isinstance(value, str):
                    try:
                        book[key] = value.encode('utf-8', errors='replace').decode('utf-8')
                    except:
                        book[key] = "Неизвестно"
                else:
                    book[key] = value
            books.append(book)
        
        return books

@tool
def save_user_preferences(user_id: int, name: str, preferred_genres: List[str] = None, 
                        preferred_authors: List[str] = None, age_limit: str = None,
                        author_origin_preference: str = None) -> bool:
    """Сохраняет или обновляет предпочтения пользователя."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_preferences 
            (user_id, name, preferred_genres, preferred_authors, age_limit, author_origin_preference)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name,
                preferred_genres = EXCLUDED.preferred_genres,
                preferred_authors = EXCLUDED.preferred_authors,
                age_limit = EXCLUDED.age_limit,
                author_origin_preference = EXCLUDED.author_origin_preference
            RETURNING user_id;
            """,
            (user_id, name, preferred_genres, preferred_authors, age_limit, author_origin_preference)
        )
        conn.commit()
        return cur.fetchone() is not None

@tool
def get_user_preferences(user_id: int) -> Dict:
    """Возвращает предпочтения пользователя."""
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM user_preferences WHERE user_id = %s;", (user_id,))
        return cur.fetchone()

@tool
def add_to_search_history(user_id: int, search_query: str, results: List[Dict]) -> bool:
    """Добавляет запрос в историю поиска пользователя."""
    conn = get_connection()
    with conn.cursor() as cur:
        result_ids = [r["id"] for r in results]

        history_entry = {
            "query": search_query,
            "results": result_ids,
            "timestamp": datetime.now().isoformat()
        }
        
        cur.execute(
            """
            UPDATE user_preferences 
            SET search_history = COALESCE(search_history, '[]'::jsonb) || %s::jsonb
            WHERE user_id = %s
            RETURNING user_id;
            """,
            (json.dumps(history_entry), user_id) 
        )
        conn.commit()
        return cur.fetchone() is not None
    
@tool
def get_random_book() -> Dict:
    """Возвращает случайную книгу из БД."""
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * FROM books 
            ORDER BY RANDOM() 
            LIMIT 1;
        """)
        return cur.fetchone() or {}

@tool
def get_random_book(genre: str = None, age_limit: str = None, author_origin: str = None) -> Dict:
    """Возвращает случайную книгу с возможностью фильтрации по жанру, возрасту и происхождению автора."""
    conn = get_connection()
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    
    if genre:
        query += " AND genre = %s"
        params.append(genre)
    if age_limit:
        query += " AND age_limit <= %s"
        params.append(age_limit)
    if author_origin:
        query += " AND author_origin = %s"
        params.append(author_origin)
    
    query += " ORDER BY RANDOM() LIMIT 1;"
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        return cur.fetchone() or {}

@tool
def get_books_count(genre: str = None) -> int:
    """Возвращает количество книг в базе с возможностью фильтрации по жанру."""
    conn = get_connection()
    with conn.cursor() as cur:
        if genre:
            cur.execute("SELECT COUNT(*) FROM books WHERE genre = %s;", (genre,))
        else:
            cur.execute("SELECT COUNT(*) FROM books;")
        return cur.fetchone()[0]