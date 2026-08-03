# Состояние mamina_nedelka_www

Срез локального репозитория: **2026-08-02**.

## Подтверждено на диске

- `index.html` — hand-coded HTML/CSS/JS без сборщика.
- `blog/` содержит индекс и 46 страниц статей.
- `../mamina_marketing/vc_content/content/seo/` содержит 46 Markdown-источников.
- `sitemap.xml` содержит URL индекса блога и страниц статей.
- Старые `apply-mobile-fixes.py`, `mobile-fixes.css` и 3.3-МБ HTML-бэкап Claude Design удалены:
  активный сайт от них не ссылался.
- Обязательный `yandex-verification` meta-тег присутствует в `index.html`.

## Не проверено

В этой ревизии не выполнялись deploy в `/srv`, изменение Caddy и внешняя проверка
`maminanedelka.ru`. Локальный состав файлов не подтверждает, что production уже содержит тот же SHA.

## Локальная валидация 2026-08-02

- `build_blog.py` разбирается Python AST без ошибок.
- Количество Markdown-источников, HTML-страниц и URL статей в sitemap совпадает: **46 / 46 / 46**.
- Локальная проверка ссылок в изменённых Markdown-файлах не нашла отсутствующих целей.
- Новый project-local skill прошёл `quick_validate.py`.

## Следующая проверка при релизе

1. Открыть локальный `index.html` на ширинах 390 и 1280 px; проверить меню, week slider,
   отзывы, reduced motion и отсутствие горизонтального overflow.
2. Проверить генератор блога и равенство количества источников/страниц.
3. После отдельного одобренного deploy проверить главную, статью, sitemap, robots и
   `https://maminanedelka.ru/health`, не меняя webhook-маршруты Caddy.
