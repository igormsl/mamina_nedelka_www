---
name: maintain-mamina-site
description: Обслуживает hand-coded лендинг и сгенерированный SEO-блог «Маминой недельки». Использовать при правке index.html, assets, build_blog.py, blog, sitemap.xml, robots.txt, CTA/атрибуции, мобильной адаптации, SEO-статей или документации сайта; включает безопасную проверку apex-домена, который совместно обслуживает Telegram webhook.
---

# Maintain Mamina Site

## Каноны

- Лендинг: `index.html` и `assets/` этого репозитория.
- Статьи: `../mamina_marketing/vc_content/content/seo/A-*.md`.
- Генератор: `build_blog.py`; результат: `blog/` и `sitemap.xml`.
- Хостинг и deploy: `README.md` и `../VPS CLAUDE CODE RULLES/12-mamina-landing.md`.
- Проверенный срез: `STATUS.md`.

## Граница apex

`maminanedelka.ru` совмещает статику и webhook. Статическая правка не меняет маршруты
`/tg/*`, `/yookassa/*` и `/health`. Изменение Caddy, deploy в `/srv` и внешний smoke — отдельные
операции после явного одобрения.

## Лендинг

1. Править `index.html` напрямую, сохраняя `yandex-verification`, CTA-метку `?start=landing`,
   reduced motion, keyboard/focus states и отсутствие горизонтального overflow.
2. Проверить desktop 1280 px и mobile 390 px; отдельно открыть burger, week slider и отзывы.
3. Для визуального изменения снять before/after по workspace-правилам скриншотов.

## Блог

1. Менять содержимое статьи в Markdown-источнике маркетингового репозитория.
2. Запустить `python3 build_blog.py` из корня сайта.
3. Сверить число `A-*.md`, `blog/*.html` без `index.html` и URL статей в `sitemap.xml`.
4. Проверить плоский URL `blog/<slug>.html`, CTA `?start=blog`, ссылку на главную и метаданные.
5. Просмотреть diff сгенерированных файлов до коммита.

## Приёмка

- Локальные источники и output совпадают по количеству и slug.
- В diff нет секретов, персональных данных и случайных probe/backup-файлов.
- Локальная проверка и production-smoke записаны раздельно.
- Документы не утверждают свежесть production без даты и фактического HTTP/deploy evidence.
