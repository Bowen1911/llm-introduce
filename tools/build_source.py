"""Regenerate TeX from the retained Pandoc JSON; requires Pandoc 3.6+."""
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
PANDOC = os.environ.get('PANDOC', 'pandoc')
doc = json.loads(Path('source.json').read_text(encoding='utf-8'))

def normalize(value):
    if isinstance(value, list): return [normalize(v) for v in value]
    if isinstance(value, dict):
        if value.get('t') == 'Image':
            value['c'][2][0] = re.sub(r'assets/media/image(\d+)\.svg', lambda m: f'assets/media/image{int(m[1])-1}.png', value['c'][2][0])
        if value.get('t') == 'Underline':
            return {'t': 'Span', 'c': [['', [], []], normalize(value['c'])]}
        return {k: normalize(v) for k, v in value.items()}
    return value

doc = normalize(doc)

def plain(x):
    if isinstance(x, list):
        return ''.join(map(plain, x))
    if isinstance(x, dict):
        if x.get('t') == 'Str': return x['c']
        if x.get('t') in ('Space', 'SoftBreak'): return ' '
        return plain(x.get('c', []))
    return ''

def write_tex(blocks, target, standalone=False):
    data = dict(doc, blocks=([b for g in groups for b in g] if standalone else blocks))
    args = [PANDOC, '-f', 'json', '-t', 'latex', '--top-level-division=chapter', '--wrap=preserve']
    if standalone:
        args += ['-s', '-V', 'documentclass=ctexbook', '-V', 'classoption=oneside',
                 '-V', 'classoption=fontset=fandol', '-V', 'fontsize=11pt',
                 '-V', 'geometry:margin=25mm', '-V', 'colorlinks=true',
                 '-V', 'linkcolor=black', '-V', 'urlcolor=blue',
                 '-V', 'mainfont=TeX Gyre Termes', '-V', 'sansfont=TeX Gyre Heros',
                 '-V', 'monofont=Latin Modern Mono', '--include-in-header=preamble.tex']
    result = subprocess.run(args, input=json.dumps(data, ensure_ascii=False), text=True,
                            encoding='utf-8', capture_output=True, check=True)
    output = result.stdout
    if standalone:
        body = '\n\n'.join(b['c'][1] for b in blocks)
        body = body.replace('\\input{chapters/frontmatter-00.tex}', '')
        cover = r'''\begin{titlepage}
\centering
\vspace*{0.2\textheight}
{\Huge\bfseries 大模型入门教材\par}
\vspace{1.5em}
{\Large 训练一个可靠的学习助手\par}
\vspace{3em}
\input{chapters/frontmatter-00.tex}
\vfill
\end{titlepage}
'''
        output = output[:output.index('\\begin{document}')] + '\\begin{document}\n\\hypersetup{pageanchor=false}\n' + cover + '\\hypersetup{pageanchor=true}\n' + body + '\n\\end{document}\n'
        output = output.replace(Path('preamble.tex').read_text(encoding='utf-8').strip(), r'\input{preamble.tex}')
    output = re.sub(r'assets/media/image(\d+)\.svg', lambda m: f'assets/media/image{int(m[1])-1}.png', output)
    output = re.sub(r'\\includegraphics\[[^\]]*\]', r'\\includegraphics[width=\\linewidth,height=0.8\\textheight,keepaspectratio]', output)
    subs = str.maketrans('₀₁₂₃₄₅₆₇₈₉ₖᵥ', '0123456789kv')
    supers = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻', '0123456789+-')
    output = re.sub('[₀₁₂₃₄₅₆₇₈₉ₖᵥ]+', lambda m: r'\ensuremath{{}_{' + m[0].translate(subs) + '}}', output)
    output = re.sub('[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+', lambda m: r'\ensuremath{{}^{' + m[0].translate(supers) + '}}', output)
    output = output.replace(r'\textgreater', r'\textgreater\allowbreak{}').replace(r'\textbackslash n', r'\textbackslash n\allowbreak{}')
    Path(target).write_text(output, encoding='utf-8')

blocks = doc['blocks']
groups = []
current = []
skip_toc = False
for b in blocks:
    if b['t'] == 'Header' and b['c'][0] == 1:
        title = plain(b['c'][2])
        if title == '目录':
            skip_toc = True
            continue
        skip_toc = False
        if current: groups.append(current)
        current = []
    if not skip_toc:
        current.append(b)
if current: groups.append(current)

inputs = []
chapter = 0
for i, group in enumerate(groups):
    heading = group[0] if group[0]['t'] == 'Header' else None
    title = plain(heading['c'][2]) if heading else ''
    if title.startswith('第') and '章' in title:
        chapter += 1
        filename = f'chapters/ch{chapter:02d}.tex'
        heading['c'][2] = [{'t': 'Str', 'c': re.sub(r'^第.+?章\s*', '', title)}]
    elif title.startswith('附录'):
        filename = 'chapters/appendix.tex'
        for b in group:
            if b['t'] == 'Header': b['c'][1][1].append('unnumbered')
    else:
        filename = f'chapters/frontmatter-{i:02d}.tex'
    for b in group:
        if b['t'] == 'Header' and b['c'][0] == 2:
            inlines = b['c'][2]
            if inlines and inlines[0]['t'] == 'Str' and re.fullmatch(r'\d+\.\d+', inlines[0]['c']):
                del inlines[0]
                if inlines and inlines[0]['t'] == 'Space': del inlines[0]
    write_tex(group, filename)
    prefix = ''
    if chapter == 1 and title.startswith('第'): prefix = '\\tableofcontents\n\\mainmatter\n'
    if title.startswith('附录'): prefix = '\\backmatter\n'
    inputs.append({'t': 'RawBlock', 'c': ['latex', prefix + '\\input{' + filename + '}']})

write_tex([{'t': 'RawBlock', 'c': ['latex', '\\frontmatter']}] + inputs, 'main.tex', True)
print(f'Generated {chapter} chapters and {len(groups)} TeX include files.')
