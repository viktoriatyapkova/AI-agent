import os
import random
import json
from typing import List, Dict
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from langchain_gigachat.chat_models import GigaChat
from tools import (
    get_book_recommendations,
    save_user_preferences,
    get_user_preferences,
    add_to_search_history,
    get_random_book,
    get_books_count
)
from database import get_connection

load_dotenv()

system_prompt = """
Ты — AI-ассистент для рекомендации книг. Твоя задача — помогать пользователям находить книги по их предпочтениям.
Ты можешь рекомендовать книги по жанру, возрастному ограничению, происхождению автора (русский/зарубежный) и ключевым словам.
Всегда предоставляй ссылку на книгу в сервисе litres.ru.
Будь дружелюбным и полезным!
Отвечай кратко и информативно.
Используй эмодзи для выразительности.
"""

class ChatState:
    def __init__(self):
        self.user_id: int = 1
        self.user_name: str = ""
        self.current_step: str = "get_name"
        self.preferences: Dict = {}
        self.last_recommendations: List[Dict] = []

def format_book(book: Dict) -> str:
    return (
        f"📖 {book['title']} - {book['author']}\n"
        f"🔹 Жанр: {book['genre']}\n"
        f"🔹 Возрастное ограничение: {book.get('age_limit', 'нет')}\n"
        f"🔹 Автор: {book['author_origin']}\n"
        f"🔹 Рейтинг: {book.get('rating', 'нет')}\n"
        f"🔹 Описание: {book.get('description', 'нет')}\n"
        f"🔗 Ссылка: {book['url']}\n"
    )

def recommend_random_book(state: ChatState, model: GigaChat, user_input: str):
    """Рекомендация случайной книги с интеллектуальными фильтрами"""
    print("\n🎲 Анализирую ваш запрос...")
    
    filters = {}
    default_filters = {
        "рандом": {},
        "случайная": {},
        "не знаю": {},
        "что почитать": {},
        "выбери": {},
        "предложи": {}
    }
    
    is_default = any(key in user_input.lower() for key in default_filters.keys())
    
    if not is_default and model:
        try:
            prompt = f"""
            Пользователь запросил: '{user_input}'. 
            Извлеки параметры для поиска случайной книги в формате JSON.
            Доступные фильтры: genre, age_limit, author_origin.
            Пример: {{"genre": "Фантастика", "age_limit": "16+"}}
            """
            response = model([SystemMessage(content=system_prompt), HumanMessage(content=prompt)])
            filters = json.loads(response.content)
            print(f"🔍 Применяю фильтры: {filters}")
        except Exception as e:
            print(f"⚠️ Не удалось разобрать запрос: {str(e)}")
            filters = {}

    book = get_random_book.invoke({
        "genre": filters.get("genre"),
        "age_limit": filters.get("age_limit"),
        "author_origin": filters.get("author_origin")
    })
    
    if book:
        print("\n✨ Вот специально для вас:")
        print(format_book(book))
        
        add_to_search_history.invoke({
            "user_id": state.user_id,
            "search_query": f"Случайная: {user_input}",
            "results": [dict(book)]
        })
        
        if model:
            try:
                prompt = f"""
                Я рекомендовал книгу: {book['title']}.
                Запрос пользователя: '{user_input}'.
                Сделай увлекательный анонс книги (2-3 предложения),
                объясни почему она подходит под запрос.
                Используй эмодзи для выразительности.
                """
                comment = model([SystemMessage(content=system_prompt), 
                              HumanMessage(content=prompt)]).content
                print(f"\n💡 Мой комментарий:\n{comment}")

                if random.random() > 0.3:  
                    similar = get_random_book.invoke({"genre": book['genre']})
                    if similar and similar['id'] != book['id']:
                        print(f"\n📚 Возможно вам понравится также: {similar['title']}")
            except Exception as e:
                print(f"\nℹ️ Не удалось получить комментарий: {str(e)}")
    else:
        print("\n😞 К сожалению, ничего не нашлось.")
        show_fallback_recommendations(state, model, user_input)

def show_fallback_recommendations(state: ChatState, model: GigaChat, user_input: str):
    """Показывает альтернативные варианты при отсутствии результатов"""
    total_books = get_books_count.invoke({})
    print(f"\n📚 В моей коллекции {total_books} книг, но по вашему запросу ничего не найдено.")
    
    if model:
        try:
            prompt = f"""
            Пользователь искал: '{user_input}'.
            Предложи 3 альтернативных варианта поиска,
            которые могут сработать в формате:
            1. Попробуйте "..."
            2. Ищите "..."
            3. Вам может понравиться "..."
            """
            advice = model([SystemMessage(content=system_prompt), 
                         HumanMessage(content=prompt)]).content
            print(f"\n💡 Попробуйте:\n{advice}")
        except Exception as e:
            print(f"\nℹ️ Не удалось получить советы: {str(e)}")

    fallback_book = get_random_book.invoke({})
    if fallback_book:
        print("\n🎲 Могу предложить случайную книгу из коллекции:")
        print(format_book(fallback_book))

def recommend_books(state: ChatState, model: GigaChat, params: Dict = None):
    """Рекомендация книг по параметрам с обработкой ошибок кодировки"""
    if not params:
        try:
            user_prefs = get_user_preferences.invoke({"user_id": state.user_id})
            if user_prefs:
                params = {
                    "genre": user_prefs.get("preferred_genres", [None])[0],
                    "age_limit": user_prefs.get("age_limit"),
                    "author_origin": user_prefs.get("author_origin_preference"),
                    "keywords": None
                }
        except Exception as e:
            print(f"\n⚠️ Ошибка загрузки предпочтений: {str(e)}")
            params = {}

    print("\n🔍 Ищу рекомендации по параметрам:")
    if params.get('genre'):
        print(f"• Жанр: {params['genre']}")
    if params.get('age_limit'):
        print(f"• Возраст: {params['age_limit']}+")
    if params.get('author_origin'):
        print(f"• Автор: {params['author_origin']}")
    if params.get('keywords'):
        print(f"• Ключевые слова: {', '.join(params['keywords'])}")

    try:
        books = []
        raw_books = get_book_recommendations.invoke(params)

        for book in raw_books:
            clean_book = {}
            for key, value in book.items():
                if isinstance(value, str):
                    try:
                        clean_book[key] = value.encode('utf-8', errors='replace').decode('utf-8')
                    except:
                        clean_book[key] = "[данные повреждены]"
                else:
                    clean_book[key] = value
            books.append(clean_book)

        state.last_recommendations = books

        if not books:
            print("\n😞 По вашим критериям ничего не найдено.")
            show_fallback_recommendations(state, model, params)
            return

        print(f"\n📚 Найдено {len(books)} книг:")
        for i, book in enumerate(books[:5], 1):
            print(f"\n{i}. {format_book(book)}")

        try:
            query = ", ".join(f"{k}:{v}" for k, v in params.items() if v)
            add_to_search_history.invoke({
                "user_id": state.user_id,
                "search_query": query,
                "results": books[:5]  
            })
        except Exception as e:
            print(f"\n⚠️ Не удалось сохранить историю: {str(e)}")

        if model and books:
            try:
                titles = ", ".join(b['title'] for b in books[:3])
                prompt = f"""Я рекомендовал книги: {titles}.
                Параметры поиска: {params}.
                Сделай краткий обзор этой подборки (2-3 предложения).
                Упомяни общие темы или особенности."""
                comment = model([SystemMessage(content=system_prompt), 
                              HumanMessage(content=prompt)]).content
                print(f"\n💡 О подборке:\n{comment}")
            except Exception as e:
                print(f"\nℹ️ Не удалось получить описание подборки: {str(e)}")

    except Exception as e:
        print(f"\n🚨 Ошибка при поиске книг: {str(e)}")
        print("Попробуйте изменить параметры поиска.")
        show_fallback_recommendations(state, model, params)

def handle_preferences_step(state: ChatState, user_input: str, model: GigaChat):
    """Обработка шагов ввода предпочтений"""
    if state.current_step == "get_genre":
        state.preferences["genre"] = user_input
        print("\n🔞 Какой возрастной лимит вас интересует? (например, 12+, 16+, 18+)")
        state.current_step = "get_age_limit"
    
    elif state.current_step == "get_age_limit":
        state.preferences["age_limit"] = user_input
        print("\n🌍 Вы предпочитаете русских или зарубежных авторов?")
        state.current_step = "get_author_origin"
    
    elif state.current_step == "get_author_origin":
        state.preferences["author_origin"] = user_input
        print("\n🔤 Какие ключевые слова вас интересуют? (например, 'вампиры, готика')")
        state.current_step = "get_keywords"
    
    elif state.current_step == "get_keywords":
        if user_input:
            state.preferences["keywords"] = [kw.strip() for kw in user_input.split(",")]

        save_user_preferences.invoke({
            "user_id": state.user_id,
            "name": state.user_name,
            "preferred_genres": [state.preferences.get("genre")],
            "age_limit": state.preferences.get("age_limit"),
            "author_origin_preference": state.preferences.get("author_origin")
        })

        print("\n✅ Ваши предпочтения сохранены!")
        if model:
            try:
                prompt = f"""
                Пользователь {state.user_name} указал предпочтения:
                Жанр: {state.preferences.get('genre')}
                Возраст: {state.preferences.get('age_limit')}
                Автор: {state.preferences.get('author_origin')}
                Ключевые слова: {state.preferences.get('keywords', [])}
                
                Напиши персональное приветственное сообщение (2-3 предложения).
                """
                welcome = model([SystemMessage(content=system_prompt), 
                              HumanMessage(content=prompt)]).content
                print(f"\n💬 {welcome}")
            except Exception as e:
                print(f"\nℹ️ {state.user_name}, будем подбирать книги по вашим вкусам!")

        recommend_books(state, model, {
            "genre": state.preferences.get("genre"),
            "age_limit": state.preferences.get("age_limit"),
            "author_origin": state.preferences.get("author_origin"),
            "keywords": state.preferences.get("keywords", [])
        })
        state.current_step = "main_menu"

def start_chat():
    """Основная функция запуска чата"""
    try:
        print("\n🔄 Подключаюсь к базе данных...")
        conn = get_connection()
        
        if not conn:
            print("❌ Ошибка подключения к БД!")
            return

        print("✅ Успешное подключение!")

        try:
            model = GigaChat(
                credentials=os.getenv("GIGACHAT_KEY"),
                scope=os.getenv("GIGACHAT_SCOPE"),
                model=os.getenv("GIGACHAT_MODEL"),
                verify_ssl_certs=False
            )
            print("🤖 GigaChat подключён!")
        except Exception as e:
            print(f"⚠️ Ошибка GigaChat: {str(e)}")
            model = None
        
        state = ChatState()
        total_books = get_books_count.invoke({})
        print(f"\n📚 Привет! Я твой книжный ассистент. В моей коллекции {total_books} книг.")
        print("Как тебя зовут?")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                if not user_input:
                    continue
                    
                if state.current_step == "get_name":
                    state.user_name = user_input
                    print(f"\n👋 Приятно познакомиться, {state.user_name}!")

                    if model:
                        try:
                            prompt = f"""
                            Приветствуй нового пользователя {state.user_name},
                            который будет искать книги. Будь дружелюбным
                            и предложи начать (1-2 предложения).
                            """
                            greeting = model([SystemMessage(content=system_prompt), 
                                          HumanMessage(content=prompt)]).content
                            print(f"\n💬 {greeting}")
                        except Exception as e:
                            print("\nℹ️ Давайте подберём вам отличные книги!")
                    
                    print("\nДавай узнаем твои предпочтения.")
                    print("Какой жанр тебе интересен? (например, фантастика, детектив, классика)")
                    state.current_step = "get_genre"
                
                elif state.current_step in ["get_genre", "get_age_limit", "get_author_origin", "get_keywords"]:
                    handle_preferences_step(state, user_input, model)
                
                elif state.current_step == "main_menu":
                    if any(word in user_input.lower() for word in ["рекомендации", "книги", "посоветуй", "что почитать"]):
                        recommend_books(state, model)
                    elif any(word in user_input.lower() for word in ["найди", "поиск", "ищи", "найти"]):
                        if model:
                            try:
                                print("\n🤖 Анализирую запрос...")
                                response = model([SystemMessage(content=system_prompt), 
                                               HumanMessage(content=f"Извлеки параметры поиска из: '{user_input}' в JSON")])
                                params = json.loads(response.content)
                                print(f"🔍 Параметры: {params}")
                                recommend_books(state, model, params)
                            except Exception as e:
                                print(f"\n⚠️ Ошибка: {str(e)}")
                                print("Попробуйте уточнить запрос, например: 'найди фантастику 16+'")
                        else:
                            print("\nℹ️ Функция поиска недоступна. Укажите параметры вручную.")
                    elif any(word in user_input.lower() for word in ["случай", "рандом", "не знаю", "выбери", "предложи"]):
                        recommend_random_book(state, model, user_input)
                    elif user_input.lower() in ["выход", "завершить", "стоп"]:
                        print("\n📖 До новых встреч! Возвращайтесь за рекомендациями.")
                        break
                    else:
                        if model:
                            try:
                                print("\n🤖 Обрабатываю запрос...")
                                response = model([SystemMessage(content=system_prompt), 
                                               HumanMessage(content=user_input)])
                                print(f"\n💬 {response.content}")
                            except Exception as e:
                                print(f"\n⚠️ Ошибка: {str(e)}")
                                print("Попробуйте: 'найди книги', 'случайная рекомендация'")
                        else:
                            print("\nℹ️ Я могу: 'рекомендовать книги', 'найти по параметрам', 'выбрать случайную'")
                        
            except (EOFError, KeyboardInterrupt):
                print("\n📖 До свидания! Заходите ещё.")
                break

    except Exception as e:
        print(f"\n🚨 Критическая ошибка: {str(e)}")
        print("Пожалуйста, перезапустите приложение")

if __name__ == "__main__":
    start_chat()