"""Verificações do gerador; execute com o ambiente opcional do PDF."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader

MODULE_PATH = Path(__file__).with_name('build_project_guide.py')


class DocumentationPdfTests(unittest.TestCase):
    def load_builder(self):
        self.assertTrue(MODULE_PATH.exists(), 'O gerador do guia atual deve existir.')
        spec = importlib.util.spec_from_file_location('project_guide', MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_markdown_preserves_port_state_and_formats_lists(self):
        builder = self.load_builder()
        flowables = builder.render_markdown(
            '# Exemplo\n\n- Primeiro item\n- Segundo item\n\n'
            '| Estado | Significado |\n| --- | --- |\n| `open\\|filtered` | Sem resposta |\n'
        )
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'teste.pdf'
            builder.GuideDocument(str(output)).build(flowables)
            text = '\n'.join(page.extract_text() for page in PdfReader(output).pages)
        for expected in ('Primeiro item', 'Segundo item', 'open|filtered', 'Sem resposta'):
            self.assertIn(expected, text)

    def test_wrapped_listing_keeps_source_line_number(self):
        builder = self.load_builder()
        lines = builder.numbered_lines('short\n' + 'x' * 180, width=60)
        self.assertTrue(lines[0].startswith('   1 '))
        self.assertTrue(lines[1].startswith('   2 '))
        self.assertTrue(lines[2].startswith('     | '))
        self.assertTrue(all(len(line) <= 60 for line in lines))


if __name__ == '__main__':
    unittest.main()
