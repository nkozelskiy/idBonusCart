# Поиск бонусной карты — FastAPI MVP

Веб-сервис для поиска номера бонусной карты по номеру телефона или фамилии.

---

## Структура проекта

```
CursorProject/
├── app/
│   ├── main.py               # Точка входа FastAPI
│   ├── database.py           # Подключение к SQLite, Base, get_db
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # Модель пользователя (логин, пароль, роль)
│   │   └── card.py           # Модель бонусной карты
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py           # GET/POST /login, GET /logout
│   │   ├── search.py         # GET/POST /search
│   │   └── admin.py          # GET/POST /admin/upload
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py   # Хэширование паролей, аутентификация
│   │   ├── search_service.py # Поиск по телефону / фамилии
│   │   └── excel_service.py  # Чтение .xlsx и загрузка в БД
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── search.html
│   │   └── admin_upload.html
│   └── static/
│       └── style.css
├── requirements.txt
└── README.md
```

---

## Быстрый старт

### 1. Клонировать / перейти в папку проекта

```bash
cd CursorProject
```

### 2. Создать и активировать виртуальное окружение

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Запустить сервер

```bash
uvicorn app.main:app --reload
```

Сервер запустится на: **http://127.0.0.1:8000**

---

## Учётные записи по умолчанию

| Логин      | Пароль        | Роль           |
|------------|---------------|----------------|
| `admin`    | `admin123`    | Администратор  |
| `employee` | `employee123` | Сотрудник      |

> Пользователи создаются автоматически при первом запуске.

---

## Страницы

| URL             | Доступ        | Описание                       |
|-----------------|---------------|--------------------------------|
| `/`             | Все           | Перенаправление на `/login`    |
| `/login`        | Все           | Вход в систему                 |
| `/logout`       | Авторизованные| Выход                          |
| `/search`       | Все роли      | Поиск бонусной карты           |
| `/admin/upload` | Только admin  | Загрузка данных из Excel       |

---

## Формат Excel-файла

Файл должен иметь расширение `.xlsx` со следующими столбцами
(принимаются русские и английские названия):

| номер карты / card_number | фамилия / last_name | телефон / phone_number |
|---------------------------|---------------------|------------------------|
| 1234567890                | Иванов              | +7 999 123-45-67       |
| 9876543210                | Петров              | 89001234567            |

При повторной загрузке дубли по `card_number` или `phone_number` **обновляются**.

---

## Переменные окружения (продакшн)

Перед деплоем замените в `app/main.py`:

```python
secret_key="CHANGE_ME_IN_PRODUCTION_32chars!!"
```

На случайную строку длиной ≥ 32 символа. Рекомендуется вынести в `.env`.
