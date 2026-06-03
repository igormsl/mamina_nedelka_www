# mamina_nedelka_www

Маркетинговый лендинг **«Мамина неделька»** — рекламирует Telegram-бот + мини-приложение.

- **Живёт на:** `https://maminanedelka.ru/` (apex), на казахстанском VPS, отдаётся Caddy как статика.
- **CTA:** ведёт в бота `https://t.me/mamina_nedelka_bot`; поддержка — `@mamina_nedelka_support_bot`.
- `index.html` — самодостаточный офлайн-файл (шрифты Bricolage Grotesque + Manrope и картинки вшиты base64). Сгенерирован в Claude Design по дизайн-системе мини-аппа.

## Архитектура хостинга (важно)

Apex `maminanedelka.ru` **одновременно** обслуживает Telegram-webhook бота и этот лендинг.
Caddy маршрутизирует по пути:

- `/tg/*`, `/yookassa/*`, `/health` → бот (`127.0.0.1:8080`) — **webhook, трогать нельзя**;
- всё остальное → статика из `/srv/maminanedelka_www/` (этот `index.html`).

Полная инструкция и процедура деплоя — в воркспейсе:
`project/VPS CLAUDE CODE RULLES/12-mamina-landing.md`.

## Обновить лендинг

1. Перегенерировать/поправить в Claude Design → экспорт Standalone HTML.
2. Заменить `index.html` здесь, закоммитить, запушить.
3. На VPS: скопировать новый `index.html` в `/srv/maminanedelka_www/` (без `sudo systemctl restart caddy` — файл подхватывается сразу, Caddy перечитывать не нужно).

## Источник

Исходник (JSX, ассеты, скриншоты, промт, инструкции) — в репозитории бота:
`project/mamina_nedelka/docs/landing/` — там `README.md` (навигатор), `claude-design-workflow.md`
(как собрать), `LANDING_PROMPT.md`, `design-system-intake/`, `generated-site/` (вывод Claude Design).
