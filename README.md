# mamina_nedelka_www

Маркетинговый лендинг **«Мамина неделька»** — рекламирует Telegram-бот + мини-приложение.

- **Живёт на:** `https://maminanedelka.ru/` (apex), на казахстанском VPS, отдаётся Caddy как статика.
- **CTA:** ведёт в бота `https://t.me/mamina_nedelka_bot`; поддержка — `@mamina_nedelka_support_bot`.
- `index.html` — **hand-coded HTML/CSS** (с 2026-06-13). Один самодостаточный файл: инлайн-CSS, SVG-иконки, шрифт Manrope (Google Fonts), ванильный JS (без React/сборки), sticky-навбар (пункты «Возможности/AI/По неделям/Отзывы/Блог/Тарифы» + бургер-меню), секции hero/возможности/AI/недели/отзывы/тарифы/футер. Полностью редактируемый — правь прямо в файле.
- **Визуальный слой (с 2026-06-14, эстетика «премиум/21st.dev»):** живой фон `#bg` — 4 дрейфующих брендовых блоба + SVG-зерно `#grain` + полоса прогресса чтения `#prog`; матово-стеклянные карточки (backdrop-blur) со spotlight-за-курсором; hero с реальными скриншотами приложения (3D-tilt по мыши + «дыхание»); **карусель отзывов тянется мышью** (pointer-drag + инерция; на тач — нативный свайп; стрелки/точки/автоскролл); **интерактивный слайдер недель 1→40** (картинка малыша + «размером как {фрукт}» + см + триместр + факт, плавающий bubble, градиентная заливка); count-up чисел AI-лимитов; кнопки с shine; мягкий scroll-reveal. Всё с поддержкой `prefers-reduced-motion` и контрастом AA, 0 горизонт-скролла на 360–1440.
- **Ассеты лендинга:** `assets/babies/b{4..40}.jpg` (33 илл. малыша для слайдера, ресайз из `../mamina_nedelka/miniapp/public/babies/`) + `assets/shots/*.jpg` (4 скрина приложения, ресайз из `../mamina_marketing/vc_content/materials/app_shots/mamina_nedelka/`). Данные недель (фрукт/см/факт) **вшиты в JS-массив `WEEKS`** внутри `index.html` — на проде бот `weeks.json` не отдаёт, поэтому при правке контента недель синхронизировать массив вручную из `../mamina_nedelka/content/weeks.json`.
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
2. Проверить рендером (playwright + chromium из воркспейсного `.venv`) — desktop 1280 + mobile 390 + меню + сетка ширин на горизонт-оверфлоу. ⚠️ scroll-reveal на IntersectionObserver + `scroll-behavior:smooth` → секции ревилятся ПОЗДНО: при скриншоте ждать ≥2 с после `scrollIntoView`, либо форсить `document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))`, иначе поймаешь `opacity:0` и решишь что баг.
3. Коммит, запушить.
4. На VPS (без sudo; Caddy перечитывать не нужно):
   ```bash
   cp index.html /srv/maminanedelka_www/
   cp -r assets /srv/maminanedelka_www/        # если менялись картинки малыша/скрины
   ```
   После деплоя проверить: `curl https://maminanedelka.ru/health` → `ok` (webhook бота жив).

## Блог (`/blog/`)

SEO-статьи для будущих мам на нашем домене (стратегия `../mamina_marketing/STRATEGY_2026-06.md`):
`https://maminanedelka.ru/blog/index.html` + `blog/<slug>.html` (**45 статей**) + `sitemap.xml`/`robots.txt`.

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
- ✅ Сайт добавлен в **Яндекс.Вебмастер** (подтверждён meta-тегом, sitemap отдан). Google
  Search Console — в планах. Источник всех статей в `mamina_marketing/`, навигация назад из
  блога — ссылка «← На сайт» в шапке.

## Источник

Лендинг и блог — **hand-coded в этом репо** (`index.html` + `build_blog.py`); правятся напрямую.
Исторические материалы прежнего воркфлоу Claude Design (intake/промты/старый вывод) лежат в репо
бота `project/mamina_nedelka/docs/landing/` — **архив, больше не используется** (бандл заменён
hand-coded версией 2026-06-13).
