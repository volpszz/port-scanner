"""Render the Portuguese study guide with ReportLab.

Run using a Python environment containing reportlab and pypdf.
Sources and output stay under docs/; production code is never changed.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import json
import math
import re
import textwrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
    Preformatted, Table, TableStyle, Flowable, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = Path(__file__).resolve().parent
W, H = A4
M = 48
WIDTH = W - 2 * M
INK = colors.HexColor('#172b3a')
TEAL = colors.HexColor('#087e8b')
MUTED = colors.HexColor('#536779')
LIGHT = colors.HexColor('#edf5f6')

for name, filename in [
    ('Body', 'LiberationSans-Regular.ttf'),
    ('BodyBold', 'LiberationSans-Bold.ttf'),
    ('BodyItalic', 'LiberationSans-Italic.ttf'),
    ('Mono', 'LiberationMono-Regular.ttf'),
]:
    pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/liberation/' + filename))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='BodyItalic', boldItalic='BodyBold')

styles = {
    'body': ParagraphStyle('body', fontName='Body', fontSize=10.3, leading=14.6,
                           textColor=INK, spaceAfter=8.5),
    'h1': ParagraphStyle('h1', fontName='BodyBold', fontSize=22, leading=26,
                         textColor=INK, spaceAfter=17, keepWithNext=True),
    'h2': ParagraphStyle('h2', fontName='BodyBold', fontSize=12.6, leading=16,
                         textColor=TEAL, spaceBefore=9, spaceAfter=8, keepWithNext=True),
    'cover': ParagraphStyle('cover', fontName='BodyBold', fontSize=42, leading=46,
                            textColor=INK, spaceBefore=10, spaceAfter=16),
    'subtitle': ParagraphStyle('subtitle', fontName='Body', fontSize=18, leading=23,
                               textColor=TEAL, spaceAfter=26),
    'small': ParagraphStyle('small', fontName='Body', fontSize=8.4, leading=11.2,
                            textColor=MUTED, spaceAfter=8),
    'cell': ParagraphStyle('cell', fontName='Body', fontSize=8.6, leading=11.6,
                           textColor=INK, spaceAfter=0),
    'code': ParagraphStyle('code', fontName='Mono', fontSize=8.1, leading=11.2,
                           textColor=INK, backColor=LIGHT, borderPadding=9,
                           spaceBefore=5, spaceAfter=13),
    'listing': ParagraphStyle('listing', fontName='Mono', fontSize=7.4, leading=10.5,
                              textColor=INK, backColor=LIGHT, borderPadding=8,
                              spaceBefore=6, spaceAfter=10),
}


def rich(text):
    text = escape(text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # URLs are clickable; keep the visible original for offline readers.
    text = re.sub(r'(https://[^\s<>]+)', r'<link href="\1" color="#087e8b">\1</link>', text)
    return text


def p(text, style='body'):
    return Paragraph(rich(text), styles[style])


class Diagram(Flowable):
    """Compact conceptual network diagrams, not packet captures."""
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.width = WIDTH
        self.height = {'layers': 157, 'endpoints': 103, 'tcp': 172, 'udp': 172, 'flow': 126}[kind]

    def draw(self):
        c = self.canv
        c.setFillColor(LIGHT)
        c.roundRect(0, 0, self.width, self.height - 5, 8, fill=1, stroke=0)
        c.setFont('Body', 8.5)
        c.setFillColor(MUTED)
        c.drawString(12, 10, 'Esquema conceitual • não representa uma captura de tráfego')

        def box(x, y, w, h, title, subtitle=''):
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.HexColor('#bed6dc'))
            c.roundRect(x, y, w, h, 5, fill=1, stroke=1)
            c.setFillColor(INK)
            c.setFont('BodyBold', 10)
            c.drawCentredString(x + w / 2, y + h / 2 + (3 if subtitle else -3), title)
            if subtitle:
                c.setFont('Body', 8.5)
                c.setFillColor(MUTED)
                c.drawCentredString(x + w / 2, y + h / 2 - 10, subtitle)

        def arrow(x1, y1, x2, y2, label=''):
            c.setStrokeColor(TEAL)
            c.setLineWidth(1.2)
            c.line(x1, y1, x2, y2)
            angle = math.atan2(y2 - y1, x2 - x1)
            for offset in (-0.5, 0.5):
                c.line(x2, y2, x2 - 7 * math.cos(angle + offset), y2 - 7 * math.sin(angle + offset))
            if label:
                c.setFont('Body', 9)
                c.setFillColor(INK)
                c.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 5, label)

        if self.kind == 'layers':
            for i, (title, subtitle) in enumerate([
                ('Aplicação', 'seu Python e os protocolos de aplicação'),
                ('Transporte', 'TCP ou UDP • portas'),
                ('Rede', 'IPv4 • endereços e rotas'),
                ('Enlace', 'Ethernet/Wi-Fi • próximo salto'),
            ]):
                box(15, 118 - i * 31, self.width - 30, 26, title + ' — ' + subtitle)
        elif self.kind == 'endpoints':
            box(15, 35, 174, 48, 'Cliente', '127.0.0.1:porta efêmera')
            box(self.width - 189, 35, 174, 48, 'Servidor TCP', '127.0.0.1:8000')
            arrow(195, 57, self.width - 195, 57)
        elif self.kind in ('tcp', 'udp'):
            left, right = 75, self.width - 75
            box(15, 124, 120, 30, 'Cliente')
            box(self.width - 135, 124, 120, 30, 'Servidor')
            c.setStrokeColor(colors.HexColor('#bed6dc'))
            c.line(left, 32, left, 120)
            c.line(right, 32, right, 120)
            if self.kind == 'tcp':
                arrow(left, 105, right, 105, '1. SYN')
                arrow(right, 76, left, 76, '2. SYN + ACK')
                arrow(left, 47, right, 47, '3. ACK')
            else:
                arrow(left, 104, right, 104, "datagrama: b'probe'")
                arrow(right, 73, left, 73, 'resposta UDP, se a aplicação responder')
                c.setFont('BodyBold', 9)
                c.setFillColor(TEAL)
                c.drawCentredString(self.width / 2, 39, 'Sem resposta no prazo: open|filtered')
        elif self.kind == 'flow':
            labels = [('Menu + alvo', 'main.py'), ('Resolver IPv4', 'gethostbyname'),
                      ('Selecionar sondas', 'TCP / UDP / BOTH')]
            boxw = (self.width - 60) / 3
            for i, (title, sub) in enumerate(labels):
                x = 12 + i * (boxw + 18)
                box(x, 66, boxw, 43, title, sub)
                if i < 2:
                    arrow(x + boxw + 2, 87, x + boxw + 16, 87)
            c.setFont('BodyBold', 10)
            c.setFillColor(INK)
            c.drawCentredString(self.width / 2, 39, 'Para cada porta: executar sondas → imprimir estados')


class GuideDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(str(filename), pagesize=A4, leftMargin=M, rightMargin=M,
                         topMargin=50, bottomMargin=47,
                         title='Redes na prática — port scanner em Python',
                         author='Material de estudo do projeto port-scanner',
                         subject='Fundamentos de redes e leitura do código TCP/UDP')
        self.addPageTemplates(PageTemplate('normal', [Frame(M, 47, WIDTH, H-97,
                                     leftPadding=0, rightPadding=0,
                                     topPadding=0, bottomPadding=0)], onPage=self.decorate))
        self.heading_counter = 0

    def beforeDocument(self):
        self.heading_counter = 0

    def decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(TEAL)
        canvas.rect(0, H-7, W, 7, fill=1, stroke=0)
        canvas.setFont('Body', 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(M, H-30, 'REDES NA PRÁTICA  /  PYTHON • TCP • UDP')
        canvas.setStrokeColor(colors.HexColor('#d8e3e7'))
        canvas.line(M, 34, W-M, 34)
        canvas.drawString(M, 21, 'Port scanner • apostila de estudo • snapshot documentado')
        canvas.drawRightString(W-M, 21, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and getattr(flowable, '_toc', False):
            title = flowable.getPlainText()
            key = f'heading-{self.heading_counter}'
            self.heading_counter += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0)
            self.notify('TOCEntry', (0, title, self.page, key))


def heading(title):
    item = p(title, 'h1')
    item._toc = True
    return item


def codeblock(text, listing=False):
    # Wrap visual lines only; appendix keeps original line numbers.
    width = 103 if listing else 95
    lines = []
    for line in text.splitlines():
        if len(line) <= width:
            lines.append(line)
        else:
            wrapped = textwrap.wrap(line, width=width, subsequent_indent='     | ',
                                    replace_whitespace=False, drop_whitespace=False,
                                    break_long_words=True, break_on_hyphens=False)
            lines.extend(wrapped)
    return Preformatted('\n'.join(lines), styles['listing' if listing else 'code'])


def render_md(section, cover=False):
    result = []
    lines = section.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                block.append(lines[i])
                i += 1
            result.append(codeblock('\n'.join(block)))
        elif line.startswith(':::diagram '):
            result.extend([Diagram(line.split()[-1]), Spacer(1, 10)])
        elif line.startswith('# '):
            if cover:
                result.extend([Spacer(1, 40), p(line[2:], 'cover')])
            else:
                result.append(heading(line[2:]))
        elif line.startswith('## '):
            result.append(p(line[3:], 'subtitle' if cover else 'h2'))
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                parts = [cell.strip().replace('open__PIPE__filtered', 'open|filtered') for cell in lines[i].strip().replace('open|filtered', 'open__PIPE__filtered').strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', cell) for cell in parts):
                    rows.append([p(cell, 'cell') for cell in parts])
                i += 1
            i -= 1
            widths = [WIDTH / len(rows[0])] * len(rows[0])
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dceff0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f8fa')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.HexColor('#bed6dc')),
            ]))
            result.extend([table, Spacer(1, 12)])
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith(('#', '```', '|', ':::')):
                i += 1
                paragraph.append(lines[i].strip())
            result.append(p(' '.join(paragraph)))
        i += 1
    return result


def main():
    source = (HERE / 'guia-redes-port-scanner.md').read_text()
    sections = source.split(':::page')
    story = render_md(sections[0], cover=True)
    story.append(PageBreak())
    story.append(p('Roteiro de estudo', 'h1'))
    story.append(p('O sumário e os marcadores do PDF permitem voltar diretamente aos capítulos. Leia os fundamentos antes de interpretar os resultados do laboratório.'))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle('toc', fontName='Body', fontSize=9.0,
                                      leading=10.5, spaceBefore=0, spaceAfter=0, textColor=INK,
                                      leftIndent=0, firstLineIndent=0, rightIndent=12)]
    story.append(toc)
    for section in sections[1:]:
        story.append(PageBreak())
        story.extend(render_md(section))

    manifest = {}
    for filename, label in [
        ('snapshot/main.py', 'Apêndice A — main.py completo'),
        ('snapshot/connection.py', 'Apêndice B — connection.py completo'),
        ('snapshot/test_connection.py', 'Apêndice C — testes completos'),
        ('labs/tcp_server.py', 'Apêndice D — servidor TCP local'),
        ('labs/udp_server.py', 'Apêndice E — servidor UDP local'),
        ('labs/probe_local.py', 'Apêndice F — cliente do laboratório'),
    ]:
        path = HERE / filename
        contents = path.read_text()
        manifest[filename] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                              'lines': len(contents.splitlines())}
        story.append(PageBreak())
        story.append(heading(label))
        story.append(p(f'Arquivo: docs/{filename}. Numeração original preservada. Linhas longas podem continuar visualmente com o marcador |.', 'small'))
        lines = contents.splitlines()
        # One listing page is enough at this scale; Preformatted may split safely.
        numbered = '\n'.join(f'{i:3}  {line}' for i, line in enumerate(lines, 1))
        story.append(codeblock(numbered, listing=True))
        if filename == 'labs/tcp_server.py':
            story.append(p('Leitura guiada: bind fixa o endpoint local; listen prepara a fila TCP; accept devolve um novo socket para o cliente. O socket de escuta continua aberto. recv vazio indica que o outro lado encerrou seu envio sem dados pendentes.'))
        elif filename == 'labs/udp_server.py':
            story.append(p('Leitura guiada: não há listen nem accept. recvfrom devolve bytes e o endereço do remetente; sendto usa esse endereço para a resposta. --silent mantém a recepção, mas suprime o envio.'))
        elif filename == 'labs/probe_local.py':
            story.append(p('Leitura guiada: argparse valida protocolo e porta; o alvo é fixo em loopback. O ajuste de sys.path permite importar connection.py da raiz quando o script é executado por caminho. Isso é uma conveniência deste laboratório, não uma exigência dos sockets.'))

    story.append(PageBreak())
    story.append(heading('Apêndice G — evidências de execução'))
    story.append(p('Saída real da execução de docs/verify_study_guide.py neste ambiente Linux. Os laboratórios usam o connection.py da raiz e os testes abaixo usam a cópia em docs/snapshot/. Servidores temporários são encerrados ao final.'))
    story.append(codeblock((HERE / 'verificacao-laboratorios.txt').read_text(), listing=True))
    story.append(p('Os estados após encerramento refletem este ambiente local, não uma garantia para todos os sistemas. O main.py atual da raiz foi preservado e não é o ponto de entrada completo avaliado aqui.'))
    story.append(p('Identificação do snapshot', 'h2'))
    for filename, metadata in manifest.items():
        story.append(p(f'{filename} — {metadata["lines"]} linhas — SHA-256: {metadata["sha256"]}', 'small'))

    output = HERE / 'guia-redes-port-scanner.pdf'
    GuideDoc(output).multiBuild(story)
    from pypdf import PdfReader
    reader = PdfReader(output)
    text = '\n\n'.join(page.extract_text() or '' for page in reader.pages)
    (HERE / 'guia-redes-port-scanner.extraido.txt').write_text(text)
    report = {'output': str(output), 'pages': len(reader.pages),
              'bytes': output.stat().st_size, 'snapshot': manifest,
              'page_text_lengths': [len(page.extract_text() or '') for page in reader.pages]}
    (HERE / 'guia-redes-port-scanner.manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
