# mamina_nedelka_www

Маркетинговый лендинг **«Мамина неделька»** — рекламирует Telegram-бот + мини-приложение.

- **Живёт на:** `https://maminanedelka.ru/` (apex), на казахстанском VPS, отдаётся Caddy как статика.
- **CTA:** ведёт в бота `https://t.me/mamina_nedelka_bot`; поддержка — `@mamina_nedelka_support_bot`.
- `index.html` — **hand-coded HTML/CSS** (с 2026-06-13). Один самодостаточный файл: инлайн-CSS, SVG-иконки, шрифт Manrope (Google Fonts), мобильное меню на ванильном JS, sticky-навбар с пунктом **«Блог»**, секции hero/возможности/AI/недели/отзывы/тарифы/футер. Полностью редактируемый — правь прямо в файле.
- ⚠️ **Старый бандл Claude Design убран** (он пересобирал документ из сериализованной строки → нельзя было добавить пункт меню или поправить вёрстку; бэкап в `_probe/index_claudedesign_backup.html`). Поэтому `apply-mobile-fixes.py` + `mobile-fixes.css` **больше НЕ нужны** (легаси, мобайл теперь нативно в `index.html`). Лендинг и блог — единый hand-coded сайт.
- ⚠️ В `<head>` обязателен `<meta name="yandex-verification" content="5de9122d74676c4f">` — без него отвалится подтверждение домена в Яндекс.Вебмастере. CTA → `t.me/mamina_nedelka_bot?start=landing` (атрибуция).

## Архитектура хостинга (важно)

Apex `maminanedelka.ru` **одновременно** обслуживает Telegram-webhook бота и этот лендинг.
Caddy маршрутизирует по пути:

- `/tg/*`, `/yookassa/*`, `/health` → бот (`127.0.0.1:8080`) — **webhook, трогать нельзя**;
- всё остальное → статика из `/srv/maminanedelka_www/` (этот `index.html`).

Полная инструкция и процедура деплоя — в воркспейсе:
`project/VPS CLAUDE CODE RULLES/12-mamina-landing.md`.

## Обновить лендинг

1. Править `index.html` напрямую (hand-coded, инлайн-CSS).
2. Проверить рендером (локальный Caddy + playwright) — desktop 1280 + mobile 390 + меню.
3. Коммит, запушить.
4. На VPS: `cp index.html /srv/maminanedelka_www/` (без sudo; Caddy перечитывать не нужно).
   Опц. ассеты: `cp -r blog/assets /srv/maminanedelka_www/blog/`.

## Блог (`/blog/`)

SEO-статьи для будущих мам на нашем домене (стратегия `../mamina_marketing/STRATEGY_2026-06.md`):
`https://maminanedelka.ru/blog/index.html` + `blog/<slug>.html` (19 статей) + `sitemap.xml`/`robots.txt`.

- **Источник статей** — `../mamina_marketing/vc_content/content/seo/A-*.md` (там и редактировать).
- **Сборка:** `python3 build_blog.py` (stdlib, идемпотентно; парсит статьи → HTML в `blog/`,
  обновляет `sitemap.xml`). Дизайн в цветах мини-аппа, шрифт Manrope (Google Fonts).
- ⚠️ **URL только плоские** (`blog/<slug>.html`): apex-Caddy сконфигурирован `try_files {path} /index.html` —
  реальный файл отдаётся, а URL-каталоги (`/blog/`, `/blog/slug/`) проваливаются в SPA-лендинг
  (проверено локальным Caddy). Не делать ссылок на `/blog/` без `index.html`.
- **Деплой (без sudo, `/srv` принадлежит igor):**
  ```bash
  cp -r blog /srv/maminanedelka_www/ && cp sitemap.xml robots.txt /srv/maminanedelka_www/
  ```
- CTA статей ведут в бота с меткой `?start=blog` (атрибуция канала).
- После первого деплоя: добавить сайт в Яндекс.Вебмастер (подтверждение — meta-тег или DNS)
  и скормить sitemap.

## Источник

Исходник (JSX, ассеты, скриншоты, промт, инструкции) — в репозитории бота:
`project/mamina_nedelka/docs/landing/` — там `README.md` (навигатор), `claude-design-workflow.md`
(как собрать), `LANDING_PROMPT.md`, `design-system-intake/`, `generated-site/` (вывод Claude Design).
