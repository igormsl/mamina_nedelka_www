#!/usr/bin/env python3
"""Original geometric illustrations, no generated anatomy or third-party imagery.
SVG is deployable as-is; optional --png uses CairoSVG from workspace for social previews.
"""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--png',action='store_true');args=p.parse_args()
COLORS={'weeks':('#e8dff0','#7c5a95'),'checkups':('#e0e9df','#63806c'),'feel':('#f3dfd8','#a66660'),'birth':('#ebe4d4','#92734e'),'life':('#e0e8eb','#597c89'),'start':('#ede5f0','#846497')}
ICONS={
'weeks':'<rect x="-95" y="-88" width="190" height="175" rx="18" fill="#fffaf4"/><path d="M-95-35H95M-48-105V-65M48-105V-65"/><path d="M-53 0h26m27 0h26m27 0h0M-53 38h26m27 0h26"/><circle cx="52" cy="45" r="35" fill="#ceb9dd" stroke="none"/><path d="m37 44 12 12 20-25"/>',
'checkups':'<rect x="-80" y="-110" width="160" height="220" rx="14" fill="#fffaf4"/><rect x="-40" y="-122" width="80" height="32" rx="12" fill="#bdd0bc"/><path d="m-47-48 10 10 18-22M-1-45h45m-91 48 10 10 18-22M-1 6h45m-91 48 10 10 18-22M-1 57h45"/>',
'feel':'<path d="M45-105a112 112 0 1 0 62 185A110 110 0 0 1 45-105" fill="#fffaf4"/><path d="m83-61 7 20 21 7-21 7-7 20-7-20-20-7 20-7ZM-85-105v28m-14-14h28" fill="#e5b9ad"/>',
'birth':'<rect x="-105" y="-57" width="210" height="155" rx="30" fill="#fffaf4"/><path d="M-43-57v-30a43 43 0 0 1 86 0v30M-105 3h210"/><rect x="-34" y="15" width="68" height="51" rx="9" fill="#ddc8a5"/><path d="M-70-53v148M70-53v148"/>',
'life':'<path d="M-87-46H62V34a74 74 0 0 1-149 0Z" fill="#fffaf4"/><path d="M62-35h31a35 35 0 0 1 0 70H62M-112 114H113M-44-120c-25 24 24 30 0 55M11-120c-25 24 24 30 0 55"/>',
'start':'<path d="M-80 111V-64a30 30 0 0 1 30-30H78V89H-50a30 30 0 0 0 0 45H78" fill="#fffaf4"/><path d="M-80 110a25 25 0 0 1 30-21M-47-57H43M-47-28H22"/><path d="M-8 54C-87 8-35-15-8 10c26-25 79-2 0 44Z" fill="#cfb9d9"/>'}
for key,(bg,stroke) in COLORS.items():
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="{bg}"/><ellipse cx="920" cy="600" rx="430" ry="320" fill="#fff" opacity=".2"/><circle cx="260" cy="70" r="190" fill="#fff" opacity=".23"/><path d="M60 490Q120 410 240 450M1020 120q65 30 100 100" fill="none" stroke="{stroke}" stroke-width="3" opacity=".3"/><g transform="translate(600 310) scale(1.5)" stroke="{stroke}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none">{ICONS[key]}</g><circle cx="350" cy="430" r="13" fill="{stroke}" opacity=".2"/><circle cx="820" cy="150" r="10" fill="{stroke}" opacity=".25"/></svg>'''
 dest=ROOT/'assets/illustrations'/f'{key}.svg';dest.write_text(svg)
 if args.png:
  import cairosvg
  cairosvg.svg2png(bytestring=svg.encode(),write_to=str(dest.with_suffix('.png')))
(ROOT/'assets/illustrations/sprout.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120"><circle cx="60" cy="60" r="58" fill="#f1eee5"/><path d="M60 102V52" stroke="#71876c" stroke-width="4" stroke-linecap="round"/><path d="M59 70C23 73 20 46 21 31 50 30 64 47 59 70" fill="#a9bda2"/><path d="M60 52C57 19 87 15 102 19 101 46 81 58 60 52" fill="#71876c"/><path d="M59 70 35 48M61 52l25-19" stroke="#f1eee5" stroke-width="2" fill="none"/></svg>''')
print('6 category covers + sprout; PNG:',args.png)
