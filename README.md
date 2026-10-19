# Мамина неделька — сайт и блог

Сайт: **https://maminanedelka.ru/**, блог: **https://maminanedelka.ru/blog/index.html**. Блог открыт для индексации 19.10.2026 в 20:08 МСК: каталог и 50 статей, 51 URL Sitemap. Главная приложения и служебные страницы сохраняют noindex. [Текущий статус](STATUS.md), [применение и откат](docs/INDEXING.md). Локальный preview — `http://localhost:8765`.

Стек сохранён: статический HTML, CSS, ванильный JavaScript, генератор Python без сторонних зависимостей. Node, CMS и клиентского фреймворка нет.

## Где редактировать

| Что | Канонический источник |
|---|---|
| Главная, контакты, редакционные принципы, политика | `templates/*.html` |
| Общая оболочка, статьи, каталог, метаданные | `build_blog.py` |
| Дизайн и взаимодействие | `assets/site.css`, `assets/site.js` |
| Тексты и статусы статей | `../mamina_marketing/blog/content/seo/A-*.md` |
| Источники медицинских сведений | `../mamina_marketing/blog/content/seo/sources.json` |
| Тематические обложки | `scripts/build_illustrations.py` → `assets/illustrations/` |
| Текущее состояние | [STATUS.md](STATUS.md) |

`index.html`, `blog/*.html`, `about.html`, `editorial.html`, `privacy.html`, `404.html`, `sitemap.xml`, `robots.txt` и `build-manifest.json` — **результат сборки**. Правки только в HTML будут потеряны. Прежние `assets/babies/` и `assets/shots/` сохранены, но новая версия их не загружает. Логотип и favicon используются из `blog/assets/`.

## Собрать и открыть

```bash
python3 build_blog.py
python3 scripts/preview.py --port 8765
```

Открыть `http://localhost:8765`, каталог — `/blog/index.html`. Preview слушает только `127.0.0.1`, выдаёт лишь публичные артефакты, закрывает `.git`, исходники и документы. Не используйте его как production-сервер. Если workspace находится на удалённой машине, нужен проброс порта 8765 на ваш компьютер.

Обычная сборка — `preview`: на всех страницах `noindex`, видимый статус подготовки, у медицинских текстов предупреждение об отсутствии рецензии. Это не готовый к выкладке публичный пакет.

Для разрешённого предварительного включения есть отдельный режим `python3 build_blog.py --public-preview --output <пустой каталог>`. Он сохраняет `noindex` и статусы рецензий, заменяя подпись локального просмотра на «Предварительная версия». Требует приёмку дизайна, разрешение включения и подготовленный backup/rollback; не отмечает остальные условия `--release` выполненными. Проверка пакета: `python3 scripts/check_site.py --root <каталог> --mode public-preview`. `build-manifest.json` хранится рядом с публичным пакетом, в web root не выкладывается.

## Проверки

```bash
python3 scripts/check_site.py
python3 -m unittest discover -s tests -v
/home/igor/projects/claudecode/.venv/bin/python scripts/check_browser.py
```

Браузерная проверка требует запущенный preview и имеющийся в workspace Playwright/Chromium. Проверяет все страницы на семи ширинах, поиск, меню, CTA, отсутствие внешних загрузок и снимает скриншоты. Evidence — `docs/evidence/`; скриншоты-инбокс — `../../screenshots/mamina_www/`. Сохраняемые кадры приёмки лежат в `docs/evidence/visual/`.

Иллюстрации — собственные SVG предметов, без генеративной анатомии. `python3 scripts/build_illustrations.py` воспроизводит SVG; опциональный `--png` требует CairoSVG и создаёт PNG для социальных превью. PNG уже включены в проект, обычная сборка не требует CairoSVG.

## SEO и URL

- Старые адреса `/blog/<slug>.html` сохранены; [карта URL](docs/url-map.csv).
- Canonical всегда на `https://maminanedelka.ru`; UTM не входит в canonical.
- Уникальные title/description, sitemap, OG/Twitter, Article/BreadcrumbList/CollectionPage/WebSite JSON-LD. Автор-врач, рецензия, рейтинги и дата первой публикации не выдуманы.
- `dateModified` берётся из `updated:` источника, не меняется при каждом запуске.
- Подтверждение Яндекса `5de9122d74676c4f` сохранено. Вход в кабинет и актуальный статус прав отдельно не проверены.
- Google Search Console подключена 19.10.2026: verification-тег сохраняется генератором и опубликован, владелец подтвердил ресурс и доступ технического аккаунта. API-сбор в mamina_marketing работает, Google пока не вернул строки статистики (`empty`); см. STATUS. Метрика и счётчик общей посещаемости не подключены.
- Preview и действующий Caddy отдают реальные 404; `/blog/` перенаправляется на `/blog/index.html`, `/index.html` — на `/`. Текущий публичный fallback описан в [порядке релиза](docs/RELEASE.md).

## Бот и публикация

CTA ведут в `t.me/mamina_nedelka_bot` с короткими метками страницы, места кнопки и разрешённого канала. Код сайта не отправляет аналитику и не хранит cookie. Что измеряется сейчас и что пока только предложено — [воронка](docs/FUNNEL.md).

Apex также обслуживает **`/tg/*`, `/yookassa/*`, `/health`**. Ни генератор, ни preview, ни работа над дизайном не изменяют эти production-маршруты.

Индексируемый выпуск требует приёмки владельца, проверки материалов, юридических данных и разрешения. После выполнения условий `python3 build_blog.py --release --output /путь/к/отдельному/каталогу` собирает индексируемую версию. Команда сама ничего не деплоит. Гейты — `release-checklist.json`; рецензии — `status: approved` и `review_evidence:` в каждой статье. Предварительное включение через `--public-preview` не заменяет эти проверки.

VPS-процедура: `../VPS CLAUDE CODE RULES/12-mamina-landing.md`, актуальный baseline — `CURRENT_STATE.md` рядом. Особенности новой сборки, backup и откат описаны в [docs/RELEASE.md](docs/RELEASE.md). Для следующего обновления собрать новый пакет, повторить backup и postflight; текущая предварительная версия уже включена.

## Подготовка к поиску — 19.10.2026

[Пошаговый порядок](docs/INDEXING.md), [риски РФ](docs/LEGAL.md),
[сведения для РКН](docs/RKN_PREPARATION.md), [рецензии статей](docs/REVIEW_QUEUE.md).
Реквизиты подтверждены; отдельный `blog-release` применён 19.10, полный `--release` остаётся отдельной задачей. Проверка готовности:
`python3 -B scripts/search_readiness.py --live`. Подготовка замороженной операции после
реальных согласований: `python3 -B scripts/prepare_indexed_release.py`.
Обе команды сами production не меняют; при незакрытых условиях возвращают код 2.

## Отдельный индексируемый блог

`python3 -B build_blog.py --blog-release --output <пустой каталог>` открывает для поиска
каталог и 50 статей, оставляя прочие страницы noindex. Sitemap содержит 51 URL.
Этот режим требует явного `blog_indexing_approved` и проверенных технических условий,
сохраняет настоящие статусы/источники и не выдаёт медицинскую рецензию за выполненную.
Проверка: `python3 -B scripts/check_site.py --root <каталог> --mode blog-release`.
Подготовка операции: `python3 -B scripts/prepare_indexed_release.py --mode blog-release`.
Живая проверка после применения: `python3 -B scripts/search_readiness.py --mode blog-release --live`.
`--release` остаётся отдельным строгим полным выпуском. Подробности — [INDEXING](docs/INDEXING.md).
