(() => {
  'use strict';
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('#navigation');
  function closeMenu() { if (!menu || !toggle) return; menu.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); }
  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open)); menu.classList.toggle('is-open', open);
  });
  menu?.addEventListener('click', e => { if (e.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') { closeMenu(); toggle.focus(); } });
  const search = document.querySelector('#article-search');
  const filters = [...document.querySelectorAll('[data-filter]')];
  const cards = [...document.querySelectorAll('[data-article]')];
  let category = 'all';
  const normalize = s => s.toLocaleLowerCase('ru').replaceAll('ё','е').trim();
  function filter() {
    const words = normalize(search.value).split(/\s+/).filter(Boolean); let visible = 0;
    cards.forEach(card => {
      const matches = (category === 'all' || card.dataset.category === category) && words.every(w => normalize(card.dataset.search).includes(w));
      card.hidden = !matches; if (matches) visible++;
    });
    document.querySelector('#result-count').textContent = `Найдено: ${visible}`;
    document.querySelector('#no-results').hidden = visible > 0;
  }
  search?.addEventListener('input', filter);
  filters.forEach(button => button.addEventListener('click', () => { category = button.dataset.filter; filters.forEach(b => b.setAttribute('aria-pressed', String(b === button))); filter(); }));
  document.querySelector('#reset-search')?.addEventListener('click', () => { search.value = ''; category = 'all'; filters.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.filter === 'all'))); filter(); search.focus(); });
  // Only a coarse, allowlisted channel is passed to Telegram. No storage, IDs, health data or network analytics.
  const channels = {telegram:'tg',threads:'th',instagram:'ig',yandex:'ya',google:'go'};
  const channel = channels[new URLSearchParams(location.search).get('utm_source')];
  if (channel) {
    document.querySelectorAll('a[data-bot]').forEach(a => { const u = new URL(a.href); const source = u.searchParams.get('start'); if (source && /^[a-z0-9_-]{1,58}$/.test(source)) { u.searchParams.set('start', `${source}_${channel}`); a.href = u.href; } });
    document.querySelectorAll('a[href^="/"]').forEach(a => { const u = new URL(a.href); if (u.pathname === '/' || u.pathname.startsWith('/blog/')) { u.searchParams.set('utm_source', new URLSearchParams(location.search).get('utm_source')); a.href = u.pathname + u.search + u.hash; } });
  }
  // Local event contract for a future consent-gated collector; currently sends nothing.
  document.addEventListener('click', e => {
    const a = e.target.closest('a[data-bot]'); if (!a) return;
    window.dispatchEvent(new CustomEvent('mamina:bot-click', {detail:{event:'bot_click', page:document.body.dataset.page, placement:a.dataset.bot, source:new URL(a.href).searchParams.get('start')}}));
  });
})();
