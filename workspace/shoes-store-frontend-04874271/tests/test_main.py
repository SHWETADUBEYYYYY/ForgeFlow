import re
from html.parser import HTMLParser

from fastapi.testclient import TestClient

from backend.main import app


class PageElements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def test_homepage_serves_html():
    response = TestClient(app).get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert 'LESS RULES.' in response.text
    assert 'Explore details' in response.text
    assert 'Unofficial concept advertisement' in response.text
    assert 'Not affiliated with or endorsed by Nike' in response.text


def test_homepage_is_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = TestClient(app).get('/')
    assert response.status_code == 200
    assert '<title>Air Studio' in response.text


def test_studio_render_has_local_materials_and_accessible_description():
    page = TestClient(app).get('/').text
    parser = PageElements()
    parser.feed(page)
    ids = {attrs.get('id') for _, attrs in parser.elements}
    assert {'upper-material', 'panel-material', 'mesh', 'lace-weave', 'contact'} <= ids
    assert 'not product photography' in page
    assert 'class="halo"' not in page
    assert 'class="orbit"' not in page
    assert 'stop-color:var(--shoe-dark)' in page
    assert 'stop-color:var(--shoe)' in page
    svg = next(attrs for tag, attrs in parser.elements if tag == 'svg')
    assert all(name in ids for name in svg['aria-labelledby'].split())
    assert not any(attrs.get('src', '').startswith(('http:', 'https:'))
                   for _, attrs in parser.elements)


def test_navigation_and_colorway_markup():
    page = TestClient(app).get('/').text
    parser = PageElements()
    parser.feed(page)
    ids = {attrs['id'] for _, attrs in parser.elements if 'id' in attrs}
    for tag, attrs in parser.elements:
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            assert attrs['href'][1:] in ids
    buttons = [attrs for tag, attrs in parser.elements if tag == 'button']
    assert len(buttons) == 3
    assert sum(button['aria-pressed'] == 'true' for button in buttons) == 1
    assert len({button['data-color'] for button in buttons}) == 3
    for button in buttons:
        assert button['aria-label'] == button['data-label']
        assert button['data-shade'].startswith('#')
    assert 'prefers-reduced-motion:reduce' in page
    assert ':focus-visible' in page
    assert any(tag == 'svg' and attrs.get('role') == 'img'
               for tag, attrs in parser.elements)
    assert not any(tag == 'img' and attrs.get('src', '').startswith('http')
                   for tag, attrs in parser.elements)


def test_material_references_and_colorway_bindings():
    page = TestClient(app).get('/').text
    parser = PageElements()
    parser.feed(page)
    ids = [attrs['id'] for _, attrs in parser.elements if 'id' in attrs]
    assert len(ids) == len(set(ids))
    # Every local paint server must resolve, including textures on the laces.
    references = set(re.findall(r'url\(#([\w-]+)\)', page))
    assert references <= set(ids)
    assert {'upper-material', 'panel-material', 'tongue-light',
            'mesh', 'lace-weave', 'contact', 'sole'} <= references
    assert any(tag == 'radialgradient' and attrs.get('id') == 'upper-material'
               for tag, attrs in parser.elements)
    assert "setProperty('--shoe', button.dataset.color)" in page
    assert "setProperty('--shoe-dark', button.dataset.shade)" in page
    assert "getElementById('color-label').textContent = button.dataset.label" in page
    assert "getElementById('shoe-title').textContent = button.dataset.label" in page
    assert "setAttribute('aria-pressed', String(swatch === button))" in page


def test_dimensional_materials_are_local_and_color_adaptive():
    # Static regression only: this does not assess rendered visual quality.
    page = TestClient(app).get('/').text
    parser = PageElements()
    parser.feed(page)
    materials = {'collar-depth', 'collar-rim', 'toe-volume', 'air-glass'}
    ids = {attrs.get('id') for _, attrs in parser.elements}
    references = set(re.findall(r'url\(#([\w-]+)\)', page))
    assert materials <= ids
    assert materials <= references
    assert 'stroke="#e6ff42"' not in page
    assert 'fill="#d9ed98"' not in page
    assert '.shoe{transform:none;animation:none}' in page


def test_rubber_and_foam_have_separate_local_materials():
    # Material wiring only; perceived depth still requires browser inspection.
    page = TestClient(app).get('/').text
    parser = PageElements()
    parser.feed(page)
    gradients = {attrs.get('id') for tag, attrs in parser.elements
                 if tag == 'lineargradient'}
    assert {'sole', 'rubber', 'air-glass'} <= gradients
    for material in ('sole', 'rubber', 'air-glass'):
        assert any(tag == 'path' and attrs.get('fill') == f'url(#{material})'
                   for tag, attrs in parser.elements)


def test_colorway_targets_are_unique_and_secondary_panels_remain_bound():
    # Guard the selectors used by browser color and reduced-motion checks.
    page = TestClient(app).get('/').text
    parser = PageElements()
    parser.feed(page)
    for target in ('shoe-upper', 'shoe-shade'):
        matches = [attrs for tag, attrs in parser.elements
                   if target in attrs.get('class', '').split()]
        assert len(matches) == 1
    panels = [attrs for tag, attrs in parser.elements
              if 'shaded-panel' in attrs.get('class', '').split()]
    assert len(panels) == 3
    assert all('stroke' not in panel for panel in panels)
    assert '.shoe-shade,.shaded-panel{fill:var(--shoe-dark);transition:fill .35s}' in page


def test_static_content_and_responsive_accessibility_contracts():
    page = TestClient(app).get('/').text
    # These checks cover the no-script document, not browser layout or execution.
    static_page = page.split('<script>')[0]
    parser = PageElements()
    parser.feed(static_page)
    assert 'LESS RULES.' in static_page
    assert 'A little louder. A little lighter.' in static_page
    assert 'Good from every angle.' in static_page
    assert 'not a product for sale' in static_page
    assert 'Original sneaker illustration' in static_page
    assert any(attrs.get('id') == 'color-label'
               and attrs.get('aria-live') == 'polite'
               for _, attrs in parser.elements)
    detail_links = [attrs for tag, attrs in parser.elements
                    if tag == 'a' and attrs.get('href') == '#details']
    assert len(detail_links) == 3
    assert page.count('@media(max-width:600px)') == 1
    assert page.count('@media(max-width:900px)') == 1
    assert 'grid-template-columns:40% 60%' in page
    assert 'aspect-ratio:1.75' in page
    assert '.swatch:focus-visible{outline:3px solid' in page
    reduced_motion = page.split('@media(prefers-reduced-motion:reduce)')[1]
    assert 'scroll-behavior:auto' in reduced_motion
    assert 'animation:none!important' in reduced_motion
    assert 'transition:none!important' in reduced_motion
