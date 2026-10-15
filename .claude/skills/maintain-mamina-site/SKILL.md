---
name: maintain-mamina-site
description: Обслуживает статический сайт и SEO-блог Маминой недельки: шаблоны, генератор, стили, CTA, медицинские источники, локальная проверка и отдельный безопасный релиз.
---

# Maintain Mamina Site

Сначала прочитать `README.md` и `STATUS.md`; количество статей и состояние production брать оттуда с учётом даты evidence.

## Каноны

- Главная и служебные страницы: `templates/*.html`; оформление: `assets/site.css`, `assets/site.js`.
- Статьи: `../mamina_marketing/blog/content/seo/A-*.md`, реестр `sources.json`.
- Генератор: `build_blog.py`. `index.html`, `blog/*.html`, служебные HTML, sitemap и robots — производные.
- Продукт: соседний repo бота только на чтение; цены и лимиты могут переопределяться runtime.
- Публикация: `docs/RELEASE.md` вместе с актуальным VPS-runbook. Сохранённая статика не доказывает включённую выдачу.

## Работа

1. Менять канонические исходники, сохраняя чужой dirty diff.
2. Проверять медицинские утверждения по первичным источникам; отмечать требуемую рецензию. Не выдумывать авторов и отзывы.
3. Собрать `python3 build_blog.py`; по умолчанию это noindex-preview.
4. Запустить `python3 scripts/check_site.py` и относящиеся к изменению тесты `python3 -m unittest discover -s tests -v`.
5. Открыть `python3 scripts/preview.py --port 8765`; браузерная проверка — workspace Python + `scripts/check_browser.py`.
6. Просмотреть реальные desktop/mobile кадры: меню, поиск и категории, недели, оглавление, FAQ, CTA, focus и overflow. Не переносить проверки удалённых слайдера и отзывов.
7. Сверить URL, Yandex verification, SEO, источник каждой статьи и сгенерированный HTML. CTA-метки определены в `docs/FUNNEL.md`.
8. Обновить существующий STATUS и документы; провести docs-semantic-postflight.

## Граница релиза

Сайт совмещён с webhook: `/tg/*`, `/yookassa/*`, `/health` должны остаться у бота. Изменение Caddy, deploy и публичное включение требуют разрешения, актуального baseline, backup и rollback. Учитывать уже данное разрешение из разговора и STATUS. Для предварительного включения используется отдельный `--public-preview --output <пустой каталог>`: noindex и отметки проверок сохраняются. Индексируемый пакет `--release` требует всех доказанных согласований; не проставлять гейты автоматически. Проверять точный пакет через `scripts/check_site.py --root <каталог> --mode public-preview` и отдельный локальный Caddy. `scripts/deploy_site.py --bundle <каталог>` выполняет только preflight; `--apply`/`--rollback` требуют sudo владельца. Read-only HTTP-проверка не доказывает Telegram/платёжный E2E. Preview, Git, deploy и пользовательская приёмка фиксируются отдельно.
