"""Gera o guia atual sem alterar a apostila histórica ou os fontes.

Dependências opcionais: docs/requirements-pdf.txt. Execute da raiz com
.venv-pdf/bin/python docs/build_project_guide.py.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import textwrap
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
SOURCE = DOCS / 'GUIA-DO-PROJETO.md'
OUTPUT = DOCS / 'guia-do-projeto.pdf'
SOURCE_FILES = (
    'main.py', 'connection.py', 'port_scanner/__init__.py',
    'port_scanner/__main__.py', 'port_scanner/config.py',
    'port_scanner/probes.py', 'port_scanner/scanner.py', 'port_scanner/cli.py',
)
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 48
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
INK = colors.HexColor('#193347')
ACCENT = colors.HexColor('#087f8c')
PALE = colors.HexColor('#edf4f7')
STYLES = {}


def configure_fonts(directory: Path) -> None:
    """Registra fontes Unicode; falha claramente se os arquivos não existirem."""
    for name, filename in (
        ('GuideBody', 'LiberationSans-Regular.ttf'),
        ('GuideBold', 'LiberationSans-Bold.ttf'),
        ('GuideMono', 'LiberationMono-Regular.ttf'),
    ):
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f'Fonte não encontrada: {path}. Use --font-dir.')
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily('GuideBody', normal='GuideBody', bold='GuideBold',
                                  italic='GuideBody', boldItalic='GuideBold')
    STYLES.update({
        'body': ParagraphStyle('body', fontName='GuideBody', fontSize=10.2,
                               leading=14.5, textColor=INK, spaceAfter=7.5),
        'h1': ParagraphStyle('h1', fontName='GuideBold', fontSize=21, leading=26,
                             textColor=INK, spaceAfter=15, keepWithNext=True),
        'h2': ParagraphStyle('h2', fontName='GuideBold', fontSize=13, leading=17,
                             textColor=ACCENT, spaceAfter=9, spaceBefore=12, keepWithNext=True),
        'h3': ParagraphStyle('h3', fontName='GuideBold', fontSize=11, leading=15,
                             textColor=INK, spaceAfter=8, spaceBefore=8, keepWithNext=True),
        'code': ParagraphStyle('code', fontName='GuideMono', fontSize=8.0, leading=11,
                               backColor=PALE, borderPadding=7, spaceBefore=6, spaceAfter=12),
        'small': ParagraphStyle('small', fontName='GuideBody', fontSize=8.5, leading=12,
                                textColor=INK, spaceAfter=9),
        'cell': ParagraphStyle('cell', fontName='GuideBody', fontSize=9, leading=12),
    })


def rich(text: str) -> str:
    """Aplica apenas o subconjunto de Markdown usado pelo guia."""
    text = escape(text.replace('\\|', '|'))
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="GuideMono">\1</font>', text)
    return text


class GuideDocument(BaseDocTemplate):
    """Documento A4 com paginação, marcadores e sumário multipasse."""

    def __init__(self, filename: str):
        if not STYLES:
            configure_fonts(Path('/usr/share/fonts/liberation'))
        super().__init__(filename, pagesize=A4, title='port-scanner — guia do projeto',
                         author='volpsz — documentação do projeto port-scanner',
                         leftMargin=MARGIN, rightMargin=MARGIN)
        frame = Frame(MARGIN, 49, CONTENT_WIDTH, PAGE_HEIGHT - 100,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate('guide', [frame], onPage=self.decorate))
        self.heading_index = 0

    def beforeDocument(self):
        self.heading_index = 0

    def decorate(self, canvas, document):
        canvas.saveState()
        canvas.setFillColor(ACCENT)
        canvas.rect(0, PAGE_HEIGHT - 7, PAGE_WIDTH, 7, fill=1, stroke=0)
        canvas.setFont('GuideBody', 8)
        canvas.setFillColor(INK)
        canvas.drawString(MARGIN, PAGE_HEIGHT - 30, 'PORT SCANNER  /  GUIA DA IMPLEMENTAÇÃO ATUAL')
        canvas.drawString(MARGIN, 25, 'Python • TCP/UDP • arquitetura • manutenção')
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 25, str(document.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if getattr(flowable, 'guide_heading', False):
            key = f'chapter-{self.heading_index}'
            self.heading_index += 1
            title = flowable.getPlainText()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0)
            self.notify('TOCEntry', (0, title, self.page, key))


def numbered_lines(source: str, width: int = 96) -> list[str]:
    """Preserva números originais; continuações visuais recebem somente |."""
    result = []
    for number, line in enumerate(source.splitlines(), 1):
        prefix = f'{number:4} '
        wrapped = textwrap.wrap(line.expandtabs(4), width=width - 7,
                                replace_whitespace=False, drop_whitespace=False,
                                break_long_words=True, break_on_hyphens=False) or ['']
        result.append(prefix + wrapped[0])
        result.extend('     | ' + segment for segment in wrapped[1:])
    return result


def code_block(source: str) -> Preformatted:
    lines = []
    for line in source.expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(line, width=94, subsequent_indent='  | ',
                                   replace_whitespace=False, drop_whitespace=False,
                                   break_long_words=True, break_on_hyphens=False) or [''])
    return Preformatted('\n'.join(lines), STYLES['code'])


def chapter(title: str) -> Paragraph:
    item = Paragraph(rich(title), STYLES['h1'])
    item.guide_heading = True
    return item


def render_markdown(source: str) -> list:
    """Renderiza títulos, parágrafos, listas, tabelas simples e blocos de código."""
    if not STYLES:
        configure_fonts(Path('/usr/share/fonts/liberation'))
    story = []
    lines = source.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line:
            continue
        if line.startswith('```'):
            block = []
            while index < len(lines) and not lines[index].strip().startswith('```'):
                block.append(lines[index])
                index += 1
            index += 1
            story.append(code_block('\n'.join(block)))
        elif line.startswith('## '):
            story.extend([Spacer(1, 18), chapter(line[3:])])
        elif line.startswith('# '):
            story.append(Paragraph(rich(line[2:]), STYLES['h1']))
        elif line.startswith('### '):
            story.append(Paragraph(rich(line[4:]), STYLES['h2']))
        elif line.startswith('|'):
            rows = []
            table_lines = [line]
            while index < len(lines) and lines[index].strip().startswith('|'):
                table_lines.append(lines[index].strip())
                index += 1
            for table_line in table_lines:
                cells = [s.strip().replace('__PIPE__', '|') for s in
                         table_line.replace('\\|', '__PIPE__').strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', cell) for cell in cells):
                    rows.append([Paragraph(rich(cell), STYLES['cell']) for cell in cells])
            table = Table(rows, colWidths=[CONTENT_WIDTH / len(rows[0])] * len(rows[0]),
                          repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PALE),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            story.extend([table, Spacer(1, 10)])
        elif line.startswith('- ') or re.match(r'^\d+\. ', line):
            if line.startswith('- '):
                text = '• ' + line[2:]
            else:
                text = line
            story.append(Paragraph(rich(text), STYLES['body']))
        else:
            paragraph = [line]
            while index < len(lines) and lines[index].strip() and not re.match(
                r'^(#|```|\||- |\d+\. )', lines[index].strip()
            ):
                paragraph.append(lines[index].strip())
                index += 1
            story.append(Paragraph(rich(' '.join(paragraph)), STYLES['body']))
    return story


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font-dir', type=Path, default=Path('/usr/share/fonts/liberation'))
    args = parser.parse_args()
    configure_fonts(args.font_dir)
    story = [Spacer(1, 65), Paragraph('port-scanner', STYLES['h1']),
             Paragraph('Guia para entender, testar e modificar o código', STYLES['h2']),
             Paragraph('Documentação em português da implementação refatorada. Inclui fundamentos, '
                       'leitura por módulo, exemplos de manutenção e fontes numerados.', STYLES['body']),
             Paragraph('Use somente em destinos próprios ou autorizados. '
                       'A apostila histórica permanece separada.', STYLES['body']), PageBreak(),
             Paragraph('Sumário', STYLES['h1'])]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle('toc', fontName='GuideBody', fontSize=10,
                                     leading=14, spaceBefore=3, spaceAfter=3)]
    story.append(toc)
    story.append(PageBreak())
    story.extend(render_markdown(SOURCE.read_text(encoding='utf-8')))
    manifest = {}
    inputs = [SOURCE.relative_to(ROOT).as_posix(), *SOURCE_FILES,
              'docs/build_project_guide.py', 'docs/requirements-pdf.txt']
    for filename in inputs:
        data = (ROOT / filename).read_bytes()
        manifest[filename] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    for filename in SOURCE_FILES:
        story.extend([PageBreak(), chapter('Código-fonte — ' + filename),
                      Paragraph('Numeração original. Uma continuação visual recebe |, sem um novo '
                                'número de linha. Use o arquivo original para editar ou executar.', STYLES['small'])])
        numbered = numbered_lines((ROOT / filename).read_text(encoding='utf-8'))
        story.append(Preformatted('\n'.join(numbered), STYLES['code']))
    GuideDocument(str(OUTPUT)).multiBuild(story)
    from pypdf import PdfReader
    reader = PdfReader(OUTPUT)
    text_lengths = [len(page.extract_text() or '') for page in reader.pages]
    if not all(text_lengths):
        raise RuntimeError('O documento contém página sem texto extraível.')
    report = {'pdf': OUTPUT.name, 'pages': len(reader.pages),
              'pdf_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
              'inputs': manifest, 'page_text_lengths': text_lengths}
    path = OUTPUT.with_suffix('.manifest.json')
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'pdf': str(OUTPUT), 'pages': len(reader.pages),
                      'manifest': str(path)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
