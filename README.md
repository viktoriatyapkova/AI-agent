# 📚 Book Recommender AI

AI-ассистент для подбора книг на основе интересов пользователя. Использует GigaChat и сохраняет историю взаимодействия в PostgreSQL.

---

## 🔍 Возможности

- 💬 Персонализированные рекомендации книг
- 🌍 Учет жанра, возрастного ограничения и происхождения автора (русский/зарубежный)
- 🔗 Автоматический подбор ссылок на книги с российских книжных платформ (litres.ru и др.)
- 🧠 Хранение истории диалога в PostgreSQL

---

## ⚙️ Как это работает

1. Пользователь вводит запрос (например: `фэнтези, 16+, зарубежный автор`)
2. GigaChat обрабатывает ввод и на основе системного промпта формирует ответ
3. История диалога сохраняется в базе данных
4. Ответ включает ссылку на книгу с российских сервисов

---

## 📁 Структура проекта

```
.
├── main.py             # Основной файл запуска ассистента
├── database.py         # Подключение к PostgreSQL и работа с памятью
├── Dockerfile          # Сборка приложения
├── docker-compose.yml  # Инфраструктура проекта
├── .env                # Переменные окружения (ключи GigaChat, доступ к PostgreSQL)
├── requirements.txt    # Зависимости проекта
├── init_db.sql         # SQL-скрипт для создания таблицы в PostgreSQL
├── models.py           # Модель данных для PostgreSQL
└── README.md           # Документация
```

---

## 🚀 Быстрый старт (через Docker)

1. Создайте файл `.env` со следующим содержимым:

```env
GIGACHAT_KEY=your_gigachat_key
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat
POSTGRES_DB=bookbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

2. Запустите проект:

```bash
docker-compose up --build
```

3. После запуска введите запрос в CLI-интерфейсе:

```
Введите запрос (например: 'фэнтези, 16+, зарубежный автор'):
> исторический роман, 18+, русский автор
```

---

## 🧠 Используемые технологии

- [Python 3.10](https://www.python.org/)
- [Langchain](https://docs.langchain.com/)
- [GigaChat](https://developers.sber.ru/docs/ru/gigachat/)
- [PostgreSQL](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## 📌 Примечания

- Проект ориентирован на пользователей в России, поэтому ссылки на книги формируются только с российских ресурсов.
- Вся история чатов сохраняется в PostgreSQL — можно доработать UI или Telegram-бота на основе этого ядра.