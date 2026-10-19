# Индексация блога

Игорь 19.10.2026 прямо разрешил открыть блог для поиска. Выпуск отделён от проверки бота.
Текущий факт применения — [STATUS](../STATUS.md); рецензии, РКН, локализация и согласия
продукта не объявляются выполненными и ведутся отдельно.

## Применённая операция 20261019T170138Z

**Применено владельцем 19.10.2026 в 20:08:12 МСК.** Публичная проверка 51/51 URL — pass, noindex отсутствует. Все 77 файлов совпадают по хешам; Caddy и зависимости проверены. [Результат](evidence/blog-release-result-2026-10-19.json), [живая проверка](evidence/blog-release-live-indexability-2026-10-19.json), [postflight](evidence/blog-release-public-postflight-2026-10-19.json).
Пакет: `/home/igor/.local/state/mamina-www/20261019T170138Z/`.
Режим `blog-release`: каталог и 50 статей — **51 индексируемый URL**.
Главная приложения, about/editorial/privacy и 404 сохраняют noindex; Sitemap содержит только блог.
Статусы `specialist_review`/`owner_review`, источники, даты редакции и честные предупреждения
не меняются на фиктивное `approved`.

Проверены 22 теста, validator 56 HTML / 50 статей / 51 URL, все 77 файлов через отдельный
локальный Caddy (HTTP, SHA-256 и нужный noindex), 6 отсутствующих/служебных путей с 404,
3 редиректа с 308. Production-кандидат прошёл validate и сравнение adapted-конфигов:
всё за пределами static fallback идентично. Backup текущих 77 файлов распакован/сверен.
[HTTP-проверка](evidence/blog-release-local-checks-2026-10-19.json),
[браузер](evidence/blog-release-browser-2026-10-19.json).

## Применение владельцем — выполнено

Ниже выполненная команда; повторно apply не запускать.

```bash
sudo python3 /home/igor/.local/state/mamina-www/20261019T170138Z/deploy_site.py --bundle /home/igor/.local/state/mamina-www/20261019T170138Z --apply
```

В текущей сессии нет sudo: конфиг и `/srv` принадлежат root. По VPS
[CLAUDE](../../VPS%20CLAUDE%20CODE%20RULES/CLAUDE.md) sudo-шаг выполняет Игорь;
пароль в чат не передавать. Это техническое применение уже разрешённой операции.

Сценарий повторно проверяет baseline, исходный web root, хеши, разрешения режима,
Caddy на диске/в памяти, сервисы и HTTP. Сохраняет root-owned backup в
`/var/backups/mamina-www/20261019T170138Z/`, устанавливает новый каталог
`/srv/mamina-www-releases/20261019T170138Z/`, атомарно переключает конфиг и делает
**reload**, без restart. Новая конфигурация выдаёт HTTP noindex только путям вне
`/blog/*.html`. Бот, `/tg/*`, `/yookassa/*`, `/health` и остальные virtual hosts идентичны.

После применения проверяются все 77 опубликованных файлов и режимы заголовков,
404 служебных путей, health/Mini App и соответствие Caddy. При ошибке выполняется
автоматический откат. Результат записывается в `result.json` рядом с пакетом.

## Откат именно этой операции

```bash
sudo python3 /home/igor/.local/state/mamina-www/20261019T170138Z/deploy_site.py --bundle /home/igor/.local/state/mamina-www/20261019T170138Z --rollback
```

Возвращает точный предыдущий Caddy и предыдущую статику с noindex, сохраняя Google-тег.
Используется root-owned запись. Если конфиг изменён другой операцией, автоматическая
перезапись отклоняется. Старый rollback 15.10 возвращает 503 — его здесь не использовать.

## Проверка после применения

```bash
python3 -B scripts/search_readiness.py --mode blog-release --live --output /tmp/mamina-blog-indexability.json
```

Проверка после применения дала код 0: 51 URL, HTTP 200, свои canonical, отсутствуют meta/HTTP noindex,
robots разрешает обход. Нахождение в индексе этим ещё не подтверждается. Google/Yandex
verification, меню, поиск и CTA сохраняются. Проверить также главную/служебные страницы:
их noindex — намеренная граница этого выпуска.

## Sitemap и поисковые кабинеты

`robots.txt` содержит `Sitemap: https://maminanedelka.ru/sitemap.xml`; карта доступна
поисковикам автоматически. Google-сборщик readonly, его права не расширялись.
Для ручной отправки: Search Console → ресурс `https://maminanedelka.ru/` → «Файлы Sitemap» →
`sitemap.xml` → «Отправить». Проверка URL → `https://maminanedelka.ru/blog/index.html` →
«Проверить опубликованный URL» → «Запросить индексирование»; затем несколько статей.
Не запрашивать индексацию главной приложения в рамках этого выпуска.

Яндекс: «Индексирование» → «Файлы Sitemap» → переобход существующего файла. При режиме
«только чтение» дождаться восстановления; ссылка в robots остаётся доступна. Затем
проверить «Страницы в поиске» и свежесть отчётов. Отправка в кабинете в этой операции
автоматически не выполняется; наличие карты не выдаётся за подтверждённую отправку.

Поисковики сами определяют включение и срок. Контроль — статус URL/страниц в кабинетах,
затем показы/клики в подключённом дашборде. Пустые строки статистики не заменять нулями.

## Последующие сборки

```bash
python3 -B build_blog.py --blog-release --output /tmp/mamina-blog-release
python3 -B scripts/check_site.py --root /tmp/mamina-blog-release --mode blog-release
python3 -B scripts/prepare_indexed_release.py --mode blog-release
```

Нужны пустой output и свежий VPS baseline; операция формируется заново. Генератор читает
реальные исходники и `blog_indexing_approved`, не проставляет проверки за владельца/врача.
Полный `--release` остаётся отдельным режимом со всеми прежними согласованиями.
Публичный `--public-preview` и локальный preview остаются полностью noindex.

Источники: [порядок выкладки](RELEASE.md),
[Google — noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing),
[Google — Sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
