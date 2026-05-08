# План защиты проекта Lab 7

## 1. Кратко о проекте

Название проекта: `Corporate Communication App`.

Это веб-приложение для корпоративной коммуникации. В нем есть:

- авторизация пользователей;
- dashboard с быстрым доступом к функциям;
- создание онлайн-встреч;
- приглашение участников на встречи;
- принятие или отклонение приглашений;
- общие и приватные чаты;
- отправка сообщений в реальном времени через WebSocket;
- загрузка файлов в чат;
- уведомления;
- видеокомнаты через LiveKit;
- хранение информации о записи встречи.

Стек проекта:

- `FastAPI` - backend и маршруты;
- `Jinja2` - HTML-шаблоны;
- `SQLAlchemy` - работа с базой данных;
- `SQLite` - локальная база данных;
- `WebSocket` - realtime-чаты и уведомления;
- `LiveKit` - видеовстречи;
- `pytest` - тесты.

Главная идея архитектуры: проект разделен на слои.

- `routes` принимают HTTP/WebSocket-запросы.
- `services` содержат бизнес-логику.
- `repositories` работают с базой данных.
- `models.py` описывает таблицы.
- `templates` и `static` отвечают за интерфейс.

## 2. Где лежит проект

Корень проекта:

```text
video/
```

Основные файлы в корне:

```text
main.py                 - точка запуска приложения
requirements.txt        - Python-зависимости
Dockerfile              - сборка Docker-образа
docker-compose.yml      - запуск app + LiveKit через Docker
Makefile                - команды make up / make down / make test
README.md               - краткая инструкция
docs/DEFENSE_GUIDE.md   - этот файл для защиты
tests/test_app.py       - автотесты
```

Основной код лежит в папке:

```text
app/
```

Структура `app/`:

```text
app/
  config.py             - настройки проекта
  database.py           - подключение к SQLite
  factory.py            - создание FastAPI-приложения
  models.py             - SQLAlchemy-модели таблиц

  routes/
    pages.py            - HTML-страницы
    api.py              - POST/API-действия
    ws.py               - WebSocket endpoints
    deps.py             - зависимости: DB, текущий пользователь

  repositories/
    users.py            - запросы к пользователям
    meetings.py         - запросы к встречам
    chats.py            - запросы к чатам
    notifications.py    - запросы к уведомлениям

  services/
    auth.py             - логика авторизации
    meetings.py         - бизнес-логика встреч
    chats.py            - бизнес-логика чатов
    files.py            - валидация и сохранение файлов
    notifications.py    - создание уведомлений
    livekit.py          - интеграция с LiveKit
    seed.py             - демо-данные

  ws/
    manager.py          - менеджер WebSocket-соединений

  templates/
    base.html           - общий layout
    login.html          - страница входа
    dashboard.html      - главная страница
    profile.html        - профиль
    meetings/
      list.html         - список и создание встреч
      detail.html       - страница конкретной встречи
    chats/
      list.html         - список чатов
      detail.html       - страница чата
    partials/
      message.html      - шаблон одного сообщения
      notification_list.html - список уведомлений

  static/
    css/app.css         - стили интерфейса
    js/chat.js          - realtime-логика чата
    js/notifications.js - realtime-уведомления
    js/livekit-room.js  - управление видеокомнатой
```

## 3. Разделение на 3 зоны

Проект удобно защищать тремя людьми.

```text
Person 1 - backend / database / auth / meetings
Person 2 - chats / WebSocket / files / notifications
Person 3 - UI / templates / LiveKit
```

Каждый человек должен не просто назвать файлы, а объяснить:

- где лежит его часть;
- какие классы и функции там есть;
- какой сценарий они реализуют;
- как эта часть связана с другими зонами.

## 4. Person 1: backend, база данных, auth, meetings

### За что отвечает Person 1

Person 1 защищает базовую backend-архитектуру:

- создание FastAPI-приложения;
- подключение к базе данных;
- SQLAlchemy-модели;
- репозитории;
- авторизацию;
- создание встреч;
- приглашение участников;
- статусы участников;
- metadata записи встречи.

### Главные файлы Person 1

```text
main.py
app/factory.py
app/config.py
app/database.py
app/models.py
app/routes/deps.py
app/routes/pages.py
app/routes/api.py
app/repositories/users.py
app/repositories/meetings.py
app/services/auth.py
app/services/meetings.py
app/services/seed.py
```

### Что находится в `main.py`

Файл:

```text
main.py
```

Главная задача: запустить приложение.

Важные строки:

```python
from app import create_app

app = create_app()
```

Что объяснять:

- `create_app()` создает объект FastAPI.
- Если файл запускается напрямую, используется `uvicorn`.
- Приложение открывается на `127.0.0.1:8000`.

### Что находится в `app/factory.py`

Файл:

```text
app/factory.py
```

Главная функция:

```python
def create_app() -> FastAPI:
```

Что она делает:

- вызывает `init_db()`;
- создает демо-данные через `seed_demo_data()`;
- создает `FastAPI`;
- подключает `SessionMiddleware`;
- подключает static-файлы;
- подключает uploads;
- подключает routers:
  - `pages_router`;
  - `api_router`;
  - `ws_router`.

Что говорить на защите:

> Здесь используется factory-подход. Приложение создается в одном месте, а все модули подключаются централизованно. Это упрощает запуск, тестирование и расширение проекта.

### Что находится в `app/config.py`

Файл:

```text
app/config.py
```

Там лежат настройки:

- `BASE_DIR` - корень проекта;
- `DATA_DIR` - папка для базы данных;
- `UPLOAD_DIR` - папка для загруженных файлов;
- `STATIC_DIR` - static-файлы;
- `TEMPLATES_DIR` - HTML-шаблоны;
- `DATABASE_URL` - путь к SQLite;
- `SECRET_KEY` - ключ сессии;
- `LIVEKIT_URL`;
- `LIVEKIT_API_KEY`;
- `LIVEKIT_API_SECRET`;
- `MAX_ATTACHMENT_BYTES`;
- `ALLOWED_ATTACHMENT_EXTENSIONS`.

Что объяснять:

- настройки собраны в одном файле;
- LiveKit берется из environment variables;
- если переменные не заданы, приложение все равно работает, но видеокомната не подключается.

### Что находится в `app/database.py`

Файл:

```text
app/database.py
```

Основные элементы:

```python
engine = create_engine(...)
SessionLocal = sessionmaker(...)
class Base(DeclarativeBase)
def init_db()
def session_scope()
```

Что они делают:

- `engine` подключается к SQLite;
- `SessionLocal` создает сессии БД;
- `Base` используется всеми SQLAlchemy-моделями;
- `init_db()` создает таблицы;
- `session_scope()` безопасно открывает/закрывает сессию.

Что говорить:

> База данных изолирована в отдельном модуле. Остальной код не создает engine напрямую, а работает через session и repositories.

### Что находится в `app/models.py`

Файл:

```text
app/models.py
```

Это описание таблиц базы данных.

Основные модели:

```text
User                 - пользователь
Meeting              - встреча
MeetingParticipant   - участник встречи
Chat                 - чат
ChatMember           - участник чата
Message              - сообщение
Attachment           - файл в сообщении
Notification         - уведомление
Recording            - информация о записи встречи
```

Главные связи:

- `Meeting` связан с `MeetingParticipant`;
- `Meeting` связан с `Recording`;
- `Chat` связан с `ChatMember`;
- `Chat` связан с `Message`;
- `Message` связан с `Attachment`;
- `Notification` связан с `User`.

Что важно сказать:

- `UniqueConstraint("meeting_id", "user_id")` не дает добавить одного пользователя в одну встречу два раза.
- `UniqueConstraint("chat_id", "user_id")` не дает добавить одного пользователя в один чат два раза.
- `cascade="all, delete-orphan"` удаляет дочерние записи вместе с родительской.
- `order_by="Message.created_at"` гарантирует правильный порядок сообщений.

### Что находится в `app/routes/deps.py`

Файл:

```text
app/routes/deps.py
```

Основные функции:

```python
get_db()
get_current_user()
optional_user()
```

Что делают:

- `get_db()` дает route handler'ам сессию базы данных.
- `get_current_user()` проверяет, что пользователь авторизован.
- `optional_user()` возвращает пользователя, если он есть в сессии, но не требует авторизацию.

Что объяснять:

> Это dependency-файл. Он убирает повторяющийся код из routes. Благодаря этому каждый endpoint может просто написать `db: Session = Depends(get_db)`.

### Что находится в `app/services/auth.py`

Файл:

```text
app/services/auth.py
```

Главный класс:

```python
class AuthService:
```

Главная функция:

```python
def login(self, username: str, password: str)
```

Что делает:

- ищет пользователя по username;
- сравнивает пароль;
- возвращает `User`, если логин успешный;
- возвращает `None`, если данные неправильные.

Что сказать:

> В учебном проекте пароли хранятся просто для демонстрации. В production нужно использовать hash, например bcrypt.

### Что находится в `app/repositories/meetings.py`

Файл:

```text
app/repositories/meetings.py
```

Основные функции:

```python
list_for_user()
upcoming_for_user()
get()
create()
add_participant()
get_participant()
save_recording()
```

Что делают:

- получают встречи пользователя;
- получают будущие встречи;
- создают встречу;
- добавляют участников;
- ищут участника встречи;
- сохраняют metadata записи.

Паттерн:

```text
Repository
```

Что сказать:

> Repository изолирует SQLAlchemy-запросы от бизнес-логики. Service не пишет сложные select-запросы напрямую.

### Что находится в `app/services/meetings.py`

Файл:

```text
app/services/meetings.py
```

Главный класс:

```python
class MeetingService:
```

Основные функции:

```python
list_for_user()
upcoming_for_user()
get()
create_meeting()
update_participation()
save_recording()
```

Что делает `create_meeting()`:

1. Очищает title.
2. Проверяет, что title не пустой.
3. Парсит дату начала.
4. Добавляет организатора в список участников.
5. Проверяет лимит: максимум 30 участников.
6. Создает встречу.
7. Генерирует `room_name` для LiveKit.
8. Добавляет участников.
9. Если включена запись, создает `Recording`.
10. Создает уведомления приглашенным пользователям.

Что делает `update_participation()`:

- проверяет статус;
- ищет участника встречи;
- меняет статус на `accepted` или `declined`;
- создает уведомление организатору.

Что говорить:

> Встречи реализованы через service layer. Route только принимает форму, а вся бизнес-логика создания встречи находится в `MeetingService`.

### Что находится в `app/services/seed.py`

Файл:

```text
app/services/seed.py
```

Функция:

```python
seed_demo_data()
```

Что делает:

- создает демо-пользователей:
  - `alice / alice123`;
  - `bob / bob123`;
  - `carol / carol123`;
- создает общий чат.

Что говорить:

> Это нужно, чтобы проект можно было сразу показать без ручного заполнения базы.

## 5. Person 2: chats, WebSocket, files, notifications

### За что отвечает Person 2

Person 2 защищает коммуникационную часть:

- общий чат;
- приватные чаты;
- отправку сообщений;
- WebSocket realtime;
- загрузку файлов;
- уведомления;
- защиту WebSocket-доступа;
- отображение новых сообщений без обновления страницы.

### Главные файлы Person 2

```text
app/services/chats.py
app/repositories/chats.py
app/services/files.py
app/services/notifications.py
app/repositories/notifications.py
app/routes/api.py
app/routes/ws.py
app/ws/manager.py
app/static/js/chat.js
app/static/js/notifications.js
app/templates/chats/list.html
app/templates/chats/detail.html
app/templates/partials/message.html
app/templates/partials/notification_list.html
```

### Что находится в `app/repositories/chats.py`

Файл:

```text
app/repositories/chats.py
```

Основные функции:

```python
list_for_user()
get()
get_general_chat()
create_chat()
add_member()
get_private_chat()
user_in_chat()
create_message()
add_attachment()
```

Что они делают:

- `list_for_user()` получает все чаты пользователя.
- `get()` получает чат с участниками, сообщениями и файлами.
- `get_general_chat()` ищет общий чат.
- `create_chat()` создает новый чат.
- `add_member()` добавляет участника.
- `get_private_chat()` проверяет, есть ли уже приватный чат между двумя людьми.
- `user_in_chat()` проверяет доступ пользователя к чату.
- `create_message()` сохраняет сообщение.
- `add_attachment()` привязывает файл к сообщению.

Что говорить:

> В репозитории нет бизнес-логики. Он отвечает только за запросы к базе.

### Что находится в `app/services/chats.py`

Файл:

```text
app/services/chats.py
```

Главный класс:

```python
class ChatService:
```

Основные функции:

```python
list_for_user()
ensure_general_chat()
create_or_get_private_chat()
send_message()
```

Что делает `list_for_user()`:

- получает чаты пользователя;
- сортирует их по последней активности;
- поэтому последний активный чат показывается выше.

Что делает `ensure_general_chat()`:

- проверяет, существует ли общий чат;
- если нет, создает `General Company Chat`;
- добавляет туда всех пользователей.

Что делает `create_or_get_private_chat()`:

- запрещает создать приватный чат с самим собой;
- проверяет, существует ли уже чат между этими двумя пользователями;
- если существует, возвращает старый;
- если нет, создает новый чат;
- добавляет двух участников;
- создает уведомление второму пользователю.

Что делает `send_message()`:

1. Проверяет, что отправитель состоит в чате.
2. Проверяет, что сообщение не пустое.
3. Проверяет лимит длины: максимум 2000 символов.
4. Создает сообщение.
5. Если есть файл, сохраняет его через `LocalFileStorageStrategy`.
6. Создает запись `Attachment`.
7. Для приватного чата создает уведомление второму участнику.
8. Возвращает созданное сообщение.

Что говорить:

> `ChatService` - это центр бизнес-логики чатов. Routes не знают, как именно создать чат или сохранить файл. Они вызывают service.

### Что находится в `app/services/files.py`

Файл:

```text
app/services/files.py
```

Главные элементы:

```python
class FileValidationError(ValueError)
class LocalFileStorageStrategy
```

Функция:

```python
save_upload()
```

Что делает:

- проверяет расширение файла;
- запрещает пустой файл;
- проверяет размер файла;
- генерирует уникальное имя через `uuid4`;
- сохраняет файл в папку `uploads/`;
- возвращает имя файла и размер.

Разрешенные расширения задаются в `app/config.py`:

```text
.txt
.md
.pdf
.png
.jpg
.jpeg
.gif
.docx
```

Паттерн:

```text
Strategy
```

Что говорить:

> Сейчас используется локальное хранение файлов. Но логика вынесена в отдельный класс, поэтому потом можно заменить стратегию на S3, Google Drive или другое хранилище.

### Что находится в `app/services/notifications.py`

Файл:

```text
app/services/notifications.py
```

Основные функции:

```python
create()
list_for_user()
mark_all_read()
```

Что делают:

- создают уведомление;
- получают последние уведомления пользователя;
- отмечают уведомления прочитанными.

Когда создаются уведомления:

- при приглашении на встречу;
- при ответе на приглашение;
- при создании приватного чата;
- при приватном сообщении.

### Что находится в `app/ws/manager.py`

Файл:

```text
app/ws/manager.py
```

Главный класс:

```python
class ConnectionManager:
```

Основные поля:

```python
chat_connections
notification_connections
```

Основные функции:

```python
connect_chat()
connect_notifications()
disconnect_chat()
disconnect_notifications()
broadcast_chat()
notify_user()
```

Что делают:

- хранят активные WebSocket-соединения;
- подключают пользователя к чату;
- отключают пользователя;
- рассылают новое сообщение всем подключенным клиентам;
- отправляют уведомление конкретному пользователю.

Что говорить:

> Это Observer-like подход. Когда появляется событие, например новое сообщение, менеджер уведомляет всех подписанных клиентов.

### Что находится в `app/routes/ws.py`

Файл:

```text
app/routes/ws.py
```

Endpoints:

```python
@router.websocket("/ws/chat/{chat_id}")
@router.websocket("/ws/notifications/{user_id}")
```

Что важно:

- WebSocket чата проверяет, что пользователь авторизован.
- Проверяет, что пользователь реально состоит в этом чате.
- Если доступа нет, соединение закрывается с code `1008`.
- WebSocket уведомлений проверяет, что пользователь подключается только к своим уведомлениям.

Что говорить:

> Это защита от ситуации, когда пользователь вручную подставит чужой chat_id и попробует читать чужой чат.

### Что находится в `app/routes/api.py` для чатов

Файл:

```text
app/routes/api.py
```

Чатовые endpoints:

```python
@router.post("/chats/private")
@router.post("/chats/{chat_id}/messages")
```

Что делает `/chats/private`:

- получает текущего пользователя;
- получает `other_user_id`;
- вызывает `ChatService.create_or_get_private_chat()`;
- если ошибка, возвращает на `/chats?error=...`;
- если успех, открывает страницу чата.

Что делает `/chats/{chat_id}/messages`:

- получает текущего пользователя;
- вызывает `ChatService.send_message()`;
- сохраняет сообщение в БД;
- получает последнее сообщение;
- формирует payload;
- вызывает `manager.broadcast_chat()`;
- отправляет уведомления через `manager.notify_user()`;
- возвращает пользователя обратно в чат.

### Что находится в `app/static/js/chat.js`

Файл:

```text
app/static/js/chat.js
```

Что делает:

- подключается к `/ws/chat/{chat_id}`;
- показывает статус:
  - `Connecting`;
  - `Live`;
  - `Offline`;
- получает новые сообщения через WebSocket;
- безопасно создает DOM-элементы через `textContent`;
- добавляет сообщение в чат без перезагрузки страницы;
- автоматически скроллит чат вниз;
- отправляет форму по `Enter`;
- `Shift+Enter` делает новую строку;
- блокирует отправку пустого сообщения.

Что важно сказать:

> Раньше опасно использовать `innerHTML` для данных из WebSocket. Сейчас сообщение строится через `createElement` и `textContent`, поэтому текст пользователя не интерпретируется как HTML.

### Что находится в `app/static/js/notifications.js`

Файл:

```text
app/static/js/notifications.js
```

Что делает:

- подключается к `/ws/notifications/{user_id}`;
- получает уведомления в реальном времени;
- добавляет новое уведомление в начало списка;
- тоже использует `textContent`, а не `innerHTML`.

### Что находится в шаблонах чата

Файлы:

```text
app/templates/chats/list.html
app/templates/chats/detail.html
app/templates/partials/message.html
```

`list.html`:

- показывает список чатов;
- показывает preview последнего сообщения;
- показывает форму создания приватного чата;
- показывает ошибку, если чат создать нельзя.

`detail.html`:

- показывает название чата;
- показывает статус WebSocket;
- показывает поток сообщений;
- показывает members;
- содержит форму отправки сообщения и файла.

`partials/message.html`:

- отвечает за HTML одного сообщения;
- выделяет свои сообщения через `message-card-own`;
- показывает attachment-ссылки.

## 6. Person 3: UI, templates, LiveKit

### За что отвечает Person 3

Person 3 защищает пользовательский интерфейс и видеовстречи:

- общий layout;
- страницы login/dashboard/profile;
- страницы встреч;
- страницы чатов;
- CSS;
- browser-side JavaScript;
- LiveKit-интеграцию;
- управление микрофоном, камерой и screen share.

### Главные файлы Person 3

```text
app/templates/base.html
app/templates/login.html
app/templates/dashboard.html
app/templates/profile.html
app/templates/meetings/list.html
app/templates/meetings/detail.html
app/templates/chats/list.html
app/templates/chats/detail.html
app/templates/partials/message.html
app/templates/partials/notification_list.html
app/static/css/app.css
app/static/js/chat.js
app/static/js/notifications.js
app/static/js/livekit-room.js
app/services/livekit.py
```

### Что находится в `app/templates/base.html`

Файл:

```text
app/templates/base.html
```

Что делает:

- задает HTML-основу всех страниц;
- подключает CSS;
- подключает HTMX;
- показывает topbar, если пользователь авторизован;
- содержит ссылки:
  - Dashboard;
  - Meetings;
  - Chats;
  - Profile;
  - Logout.

Что говорить:

> Все страницы наследуются от `base.html`, поэтому общий layout не дублируется.

### Что находится в `app/templates/login.html`

Файл:

```text
app/templates/login.html
```

Что делает:

- показывает форму входа;
- показывает demo accounts;
- показывает ошибку при неправильном пароле.

Демо-аккаунты:

```text
alice / alice123
bob / bob123
carol / carol123
```

### Что находится в `app/templates/dashboard.html`

Файл:

```text
app/templates/dashboard.html
```

Что показывает:

- приветствие пользователя;
- быстрые действия;
- upcoming meetings;
- notifications;
- recent chats;
- форму создания приватного чата.

Что объяснять:

> Dashboard объединяет основные функции проекта: встречи, чаты и уведомления.

### Что находится в `app/templates/meetings/list.html`

Файл:

```text
app/templates/meetings/list.html
```

Что делает:

- показывает список встреч;
- показывает форму создания встречи;
- позволяет выбрать участников;
- позволяет включить recording metadata.

Поля формы:

- title;
- description;
- start time;
- duration;
- participants;
- recording enabled.

### Что находится в `app/templates/meetings/detail.html`

Файл:

```text
app/templates/meetings/detail.html
```

Что показывает:

- название встречи;
- описание;
- дату начала;
- организатора;
- длительность;
- room name;
- provider `LiveKit`;
- кнопки:
  - `Join room`;
  - `Mic`;
  - `Camera`;
  - `Share screen`;
  - `Leave`;
- список участников;
- статусы участников;
- блок recording metadata.

Что важно:

- если LiveKit не настроен, показывается сообщение об ошибке;
- если LiveKit настроен, можно получить token и подключиться к комнате.

### Что находится в `app/services/livekit.py`

Файл:

```text
app/services/livekit.py
```

Главные элементы:

```python
class LiveKitRoomConfig
class LiveKitConfigurationError
class LiveKitFacade
```

Основные функции:

```python
build_room_config()
generate_room_name()
generate_participant_token()
```

Что делает `build_room_config()`:

- подготавливает room name;
- возвращает server URL;
- возвращает display name;
- показывает, настроен LiveKit или нет.

Что делает `generate_room_name()`:

- создает уникальное имя комнаты по meeting id и title.

Что делает `generate_participant_token()`:

- проверяет наличие `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`;
- создает JWT-токен для участника;
- дает право подключиться к конкретной комнате.

Паттерн:

```text
Facade
```

Что говорить:

> `LiveKitFacade` скрывает детали работы с LiveKit SDK. Остальной проект не знает, как именно генерируется token.

### Что находится в `app/static/js/livekit-room.js`

Файл:

```text
app/static/js/livekit-room.js
```

Что делает:

- проверяет, настроен ли LiveKit;
- блокирует кнопки, если LiveKit не настроен;
- запрашивает token через `/api/livekit/token`;
- создает `new livekit.Room()`;
- подключается к комнате;
- включает камеру и микрофон;
- отображает видео участников;
- подключает удаленные audio tracks;
- не проигрывает локальный audio track, чтобы пользователь не слышал сам себя;
- позволяет включать/выключать микрофон;
- позволяет включать/выключать камеру;
- позволяет включать/выключать screen sharing;
- очищает интерфейс при выходе.

Что обязательно сказать:

> Локальный микрофон публикуется в комнату, но не проигрывается у самого пользователя. Поэтому другие участники слышат пользователя, но он не слышит сам себя.

### Что находится в `app/static/css/app.css`

Файл:

```text
app/static/css/app.css
```

Что содержит:

- layout страниц;
- стили topbar;
- panels/cards;
- forms/buttons;
- grid для meeting и chat pages;
- стили видеокомнаты;
- стили сообщений;
- статус WebSocket;
- responsive rules для мобильных экранов.

Что говорить:

> CSS один общий, чтобы все страницы выглядели единообразно.

## 7. API и маршруты проекта

### Page routes

Файл:

```text
app/routes/pages.py
```

Основные routes:

```text
GET  /                    - redirect на login или dashboard
GET  /login               - страница входа
POST /login               - авторизация
POST /logout              - выход
GET  /dashboard           - dashboard
GET  /profile             - профиль
GET  /meetings            - список встреч
GET  /meetings/{id}       - страница встречи
GET  /chats               - список чатов
GET  /chats/{id}          - страница чата
```

### API routes

Файл:

```text
app/routes/api.py
```

Основные routes:

```text
POST /api/meetings                  - создать встречу
POST /api/meetings/{id}/status      - принять/отклонить приглашение
POST /api/meetings/{id}/recording   - сохранить metadata записи
POST /api/chats/private             - создать/открыть приватный чат
POST /api/chats/{id}/messages       - отправить сообщение/файл
POST /api/livekit/token             - получить token для LiveKit
```

### WebSocket routes

Файл:

```text
app/routes/ws.py
```

Routes:

```text
WS /ws/chat/{chat_id}
WS /ws/notifications/{user_id}
```

## 8. Паттерны проектирования

### Repository

Файлы:

```text
app/repositories/users.py
app/repositories/meetings.py
app/repositories/chats.py
app/repositories/notifications.py
```

Смысл:

- все SQL-запросы вынесены из routes;
- бизнес-логика не смешивается с persistence-логикой.

### Service Layer

Файлы:

```text
app/services/auth.py
app/services/meetings.py
app/services/chats.py
app/services/notifications.py
```

Смысл:

- routes принимают request;
- services выполняют бизнес-логику;
- repositories работают с БД.

### Facade

Файл:

```text
app/services/livekit.py
```

Смысл:

- `LiveKitFacade` скрывает сложность LiveKit SDK;
- остальной код вызывает простые методы.

### Strategy

Файл:

```text
app/services/files.py
```

Смысл:

- сейчас файлы сохраняются локально;
- в будущем стратегию можно заменить без изменения `ChatService`.

### Observer-like realtime

Файлы:

```text
app/ws/manager.py
app/routes/ws.py
app/static/js/chat.js
app/static/js/notifications.js
```

Смысл:

- клиент подписывается на WebSocket;
- backend отправляет событие;
- браузер сразу обновляет интерфейс.

## 9. Сценарий демонстрации на защите

### Шаг 1. Запуск проекта

Без Docker:

```powershell
cd d:\project7\video
$env:LIVEKIT_URL="ws://127.0.0.1:7880"
$env:LIVEKIT_API_KEY="devkey"
$env:LIVEKIT_API_SECRET="secret"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Открыть:

```text
http://127.0.0.1:8000
```

### Шаг 2. Войти в систему

Аккаунт:

```text
alice / alice123
```

Показать:

- login page;
- dashboard;
- recent chats;
- notifications.

### Шаг 3. Создать встречу

Открыть:

```text
Meetings
```

Создать встречу:

- title: `Planning`;
- start time: любая будущая дата;
- duration: `30`;
- participants: `Bob Smith`, `Carol Davis`;
- recording enabled: по желанию.

Объясняет Person 1:

- route `/api/meetings`;
- `MeetingService.create_meeting()`;
- таблицы `Meeting`, `MeetingParticipant`, `Recording`;
- уведомления для приглашенных.

### Шаг 4. Принять приглашение

Выйти из Alice.

Войти:

```text
bob / bob123
```

Открыть встречу и нажать:

```text
Accept
```

Объясняет Person 1:

- route `/api/meetings/{meeting_id}/status`;
- `MeetingService.update_participation()`;
- статус `accepted`;
- уведомление организатору.

### Шаг 5. Показать чаты

Открыть:

```text
Chats
```

Создать приватный чат.

Отправить:

- обычное сообщение;
- сообщение с файлом.

Объясняет Person 2:

- `ChatService.create_or_get_private_chat()`;
- `ChatService.send_message()`;
- `LocalFileStorageStrategy.save_upload()`;
- `manager.broadcast_chat()`;
- WebSocket `/ws/chat/{chat_id}`.

### Шаг 6. Показать realtime

Открыть два браузера или две вкладки:

- в одной Alice;
- в другой Bob.

Отправить сообщение.

Показать:

- сообщение появляется без refresh;
- статус чата `Live`;
- уведомление приходит в dashboard.

Объясняет Person 2:

- `chat.js`;
- `notifications.js`;
- `ConnectionManager`.

### Шаг 7. Показать LiveKit

Открыть meeting detail.

Нажать:

```text
Join room
```

Показать:

- запрос на доступ к камере/микрофону;
- кнопки `Mic`, `Camera`, `Share screen`, `Leave`;
- отсутствие echo: пользователь не слышит сам себя.

Объясняет Person 3:

- `LiveKitFacade.generate_participant_token()`;
- route `/api/livekit/token`;
- `livekit-room.js`;
- почему локальный audio track не воспроизводится самому пользователю.

### Шаг 8. Показать тесты

Команда:

```powershell
python -m pytest -q
```

Что покрыто тестами:

- login success/failure;
- redirect protected pages;
- создание встречи;
- лимит 30 участников;
- принятие приглашения;
- private chat idempotency;
- запрет private chat с самим собой;
- сортировка чатов по последнему сообщению;
- отправка сообщений;
- запрет пустого сообщения;
- запрет слишком длинного сообщения;
- upload validation;
- WebSocket broadcast;
- запрет WebSocket без авторизации;
- уведомления;
- LiveKit config.

## 10. Что каждый человек говорит на защите

### Person 1 - текст выступления

> Я отвечал за backend-ядро проекта: базу данных, модели, авторизацию и встречи. Основные файлы моей части лежат в `app/models.py`, `app/database.py`, `app/repositories`, `app/services/meetings.py`, `app/services/auth.py`, а routes находятся в `app/routes/pages.py` и `app/routes/api.py`.

> В `models.py` описаны таблицы: пользователи, встречи, участники встреч, чаты, сообщения, файлы, уведомления и записи. Для работы с базой используется SQLAlchemy и SQLite.

> Для архитектуры использованы Repository и Service Layer. Repository отвечает за запросы к базе, а Service отвечает за бизнес-логику. Например, создание встречи находится в `MeetingService.create_meeting()`: там проверяется title, дата, лимит участников, добавляется организатор, создаются участники и уведомления.

> Авторизация находится в `AuthService`. Пользователь логинится, его id сохраняется в session, а `get_current_user()` проверяет доступ к защищенным страницам.

### Person 2 - текст выступления

> Я отвечал за чаты, WebSocket, файлы и уведомления. Основные файлы моей части: `app/services/chats.py`, `app/repositories/chats.py`, `app/services/files.py`, `app/ws/manager.py`, `app/routes/ws.py`, `app/static/js/chat.js`, `app/static/js/notifications.js`.

> Чаты бывают general и private. General chat создается автоматически в `seed_demo_data()`, а private chat создается через `ChatService.create_or_get_private_chat()`. Если чат уже существует, новый не создается.

> Отправка сообщений находится в `ChatService.send_message()`. Там проверяется, что пользователь состоит в чате, сообщение не пустое, длина не больше 2000 символов, а файл проходит проверку расширения и размера.

> Realtime работает через WebSocket. На backend соединениями управляет `ConnectionManager`, а на frontend `chat.js` получает сообщения и добавляет их в DOM без обновления страницы. Также WebSocket проверяет авторизацию и не дает подключиться к чужому чату.

### Person 3 - текст выступления

> Я отвечал за UI, шаблоны и LiveKit. Основные файлы моей части: `app/templates`, `app/static/css/app.css`, `app/static/js/livekit-room.js`, `app/services/livekit.py`.

> Все страницы наследуются от `base.html`. Dashboard показывает встречи, уведомления и последние чаты. Страницы встреч находятся в `templates/meetings`, страницы чатов - в `templates/chats`.

> LiveKit-интеграция разделена на backend и frontend. Backend часть находится в `LiveKitFacade`, где генерируется room name и participant token. Frontend часть находится в `livekit-room.js`, где создается LiveKit room, подключается пользователь, включается камера, микрофон и screen sharing.

> Важная деталь: локальный audio track не проигрывается самому пользователю, чтобы не было эффекта, когда человек слышит сам себя. Но микрофон публикуется в комнату, поэтому другие участники его слышат.

## 11. Типовые вопросы и ответы

### Почему проект разделен на services и repositories?

Чтобы не смешивать HTTP-код, бизнес-логику и SQL-запросы. Routes принимают request, services принимают решения, repositories работают с базой.

### Почему SQLite?

Для лабораторной работы SQLite достаточно: база локальная, не требует отдельного сервера и легко запускается. При необходимости можно заменить `DATABASE_URL` на PostgreSQL.

### Почему WebSocket?

WebSocket нужен для realtime: новые сообщения и уведомления приходят без обновления страницы.

### Как защищены чаты?

Backend проверяет, что пользователь состоит в чате. Это есть и при отправке сообщения, и при WebSocket-подключении.

### Где сохраняются файлы?

Файлы сохраняются в папку:

```text
uploads/
```

В базе хранится:

- оригинальное имя;
- сохраненное имя;
- content type;
- размер;
- связь с сообщением.

### Почему LiveKit вынесен в отдельный класс?

Это Facade. Остальной проект не должен знать детали SDK, JWT-токенов и grants. Он вызывает простые методы `LiveKitFacade`.

### Что будет, если LiveKit не настроен?

Обычные функции проекта работают: login, meetings, chats, files. На странице встречи кнопки LiveKit будут disabled или token endpoint вернет ошибку конфигурации.

### Как проверить проект?

Команда:

```powershell
python -m pytest -q
```

Ожидаемый результат:

```text
16 passed
```

## 12. Быстрый список файлов по людям

### Person 1

```text
main.py
app/factory.py
app/config.py
app/database.py
app/models.py
app/routes/deps.py
app/routes/pages.py
app/routes/api.py
app/repositories/users.py
app/repositories/meetings.py
app/services/auth.py
app/services/meetings.py
app/services/seed.py
```

### Person 2

```text
app/repositories/chats.py
app/repositories/notifications.py
app/services/chats.py
app/services/files.py
app/services/notifications.py
app/routes/ws.py
app/ws/manager.py
app/static/js/chat.js
app/static/js/notifications.js
app/templates/chats/list.html
app/templates/chats/detail.html
app/templates/partials/message.html
app/templates/partials/notification_list.html
```

### Person 3

```text
app/templates/base.html
app/templates/login.html
app/templates/dashboard.html
app/templates/profile.html
app/templates/meetings/list.html
app/templates/meetings/detail.html
app/static/css/app.css
app/static/js/livekit-room.js
app/services/livekit.py
```

## 13. Финальный порядок защиты

1. Person 1 показывает архитектуру, базу, авторизацию и встречи.
2. Person 2 показывает чаты, WebSocket, файлы и уведомления.
3. Person 3 показывает UI и LiveKit.
4. Команда вместе показывает end-to-end сценарий:
   - login;
   - meeting;
   - invite;
   - accept;
   - chat;
   - file;
   - notification;
   - LiveKit room.
5. В конце показать тесты.

Главная мысль защиты:

> Проект разделен на независимые зоны, но они связаны через общую архитектуру: routes -> services -> repositories -> database, а UI взаимодействует с backend через HTTP и WebSocket.
