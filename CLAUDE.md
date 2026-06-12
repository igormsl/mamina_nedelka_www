# CLAUDE.md — mamina_nedelka_www

Маркетинговый **лендинг** «Мамина неделька» (рекламирует Telegram-бот + мини-апп). Живёт на `https://maminanedelka.ru/` (apex), казахстанский VPS, отдаётся Caddy как статика. Свой git-репо `igormsl/mamina_nedelka_www`.

**Источник правды — [README.md](README.md). Прочитай его перед любой работой.** Этот файл — карта + критичное правило безопасности.

## ⚠️ Главная опасность — apex со-хостит webhook бота

Apex `maminanedelka.ru` **одновременно** обслуживает живой Telegram-webhook прод-бота И этот лендинг. Caddy маршрутизирует по пути:

- `/tg/*`, `/yookassa/*`, `/health` → бот (`127.0.0.1:8080`) — **НЕ ТРОГАТЬ, сломаешь приём оплат и сообщений**;
- всё остальное → статика `/srv/maminanedelka_www/` (этот `index.html`).

Любая правка Caddy-конфига apex может убить вебхук. Деплой/откат лендинга — `../VPS CLAUDE CODE RULLES/12-mamina-landing.md`.

## Как обновить лендинг

1. Перегенерировать/поправить в Claude Design → экспорт Standalone HTML → заменить `index.html`.
2. **После каждой генерации:** `python3 apply-mobile-fixes.py` (впаивает `mobile-fixes.css` ВНУТРЬ сериализованной строки бандла — простой `<style>` стирается).
3. Коммит + push, затем на VPS `cp index.html /srv/maminanedelka_www/` (без рестарта Caddy — файл подхватывается сразу).

## Связь

Исходник (JSX, ассеты, промт) — в репо бота: `project/mamina_nedelka/docs/landing/`. CTA → `t.me/mamina_nedelka_bot`; поддержка → `@mamina_nedelka_support_bot`.
