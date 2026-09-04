# CLAUDE.md — mamina_nedelka_www

Маркетинговый **лендинг** «Мамина неделька» (рекламирует Telegram-бот + мини-апп). Его адрес — `https://maminanedelka.ru/` (apex), статика хранится на VPS. Свой git-репо `igormsl/mamina_nedelka_www`.

> ⏸️ **С 10.08.2026 сайт отключён.** Лендинг и блог отдают `503`; блок статики в Caddy заменён на
> `respond`, файлы в `/srv` и этот репозиторий не тронуты. `/health` и оболочка Mini App доступны;
> end-to-end сценарии Telegram и ЮKassa этой HTTP-проверкой не подтверждены.
> Детали и порядок возврата — [STATUS.md](STATUS.md). Перед любым деплоем сначала верни сайт,
> иначе выкатишь в недоступный apex.

**Источник правды — [README.md](README.md). Прочитай его перед любой работой.** Этот файл — карта + критичное правило безопасности.

## ⚠️ Главная опасность — apex со-хостит webhook бота

Apex `maminanedelka.ru` **одновременно** обслуживает живой Telegram-webhook прод-бота И этот лендинг. Caddy маршрутизирует по пути:

- `/tg/*`, `/yookassa/*`, `/health` → бот (`127.0.0.1:8080`) — **НЕ ТРОГАТЬ, сломаешь приём оплат и сообщений**;
- всё остальное → статика `/srv/maminanedelka_www/` (этот `index.html`).

Любая правка Caddy-конфига apex может убить вебхук. Деплой/откат лендинга — `../VPS CLAUDE CODE RULES/12-mamina-landing.md`.

## Блог `/blog/` (SEO-статьи)

Статика рядом с лендингом: `blog/<slug>.html` (источник — `../mamina_marketing/vc_content/content/seo/`,
сборка `python3 build_blog.py`, деплой `cp -r blog sitemap.xml robots.txt /srv/maminanedelka_www/` без sudo).
⚠️ URL только плоские `.html` — каталоги (`/blog/`) проваливаются в SPA-лендинг (см. README § Блог).

## Как обновить лендинг

С 2026-06-13 `index.html` — **hand-coded** (не Claude Design), ванильный JS без сборки. Правь файл напрямую, проверь рендером (playwright из воркспейсного `.venv`: desktop 1280 + mobile 390 + меню + сетка ширин на оверфлоу), коммить+push, затем на VPS `cp index.html /srv/maminanedelka_www/` (+ `cp -r assets ...` если менялись картинки) — без рестарта Caddy. После деплоя: `curl https://maminanedelka.ru/health` → `ok`.

Метатег `<meta name="yandex-verification">` — обязательный инвариант `<head>`. Мобильные стили
живут в `index.html`; отдельный патч старого бандла удалён.

**Визуальный слой (с 2026-06-14):** живой aurora-фон (`#bg` блобы + `#grain` + `#prog`), стеклянные карточки со spotlight, hero с реальными скринами приложения + 3D-tilt, **карусель отзывов тянется мышью** (drag+инерция), **интерактивный слайдер недель 1→40**, count-up, scroll-reveal. Всё ванилью, `prefers-reduced-motion` + AA + 0 горизонт-скролла 360–1440. Подробности и грабли (IO-reveal + smooth-scroll = поздний ревил при playwright-проверке) — в [README.md](README.md).

**Ассеты** в `assets/babies/` (илл. малыша для слайдера) + `assets/shots/` (скрины приложения). Данные недель **вшиты в JS-массив `WEEKS`** в `index.html` (на проде бот `weeks.json` не отдаёт) — при правке контента синхронизировать вручную из `../mamina_nedelka/content/weeks.json`.

## Источник и связь

Рабочий исходник лендинга и блога находится в этом репозитории: `index.html`, `assets/`,
`build_blog.py`, `blog/`, `sitemap.xml` и `robots.txt`. Папка
`../mamina_nedelka/docs/landing/` — только исторический архив прежнего Claude Design-процесса.
CTA → `t.me/mamina_nedelka_bot`; поддержка → `@mamina_nedelka_support_bot`.

Локальный статус и граница внешней проверки — [STATUS.md](STATUS.md).
