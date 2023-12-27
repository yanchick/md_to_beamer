#!/usr/bin/python3.11

import sys
import cairosvg
import os
import base64
import zlib
import requests
from pandocfilters import toJSONFilter, Para, Image
from pandocfilters import get_filename4code, get_caption, get_extension

# Diagram types that will be supported. 
DIAGRAM_TYPES = ['blockdiag', 'bpmn', 'bytefield', 'seqdiag', 'actdiag',
                 'nwdiag', 'packetdiag', 'rackdiag', 'c4plantuml', 'ditaa',
                 'erd', 'excalidraw', 'graphviz', 'mermaid', 'nomnoml',
                 'plantuml', 'svgbob', 'umlet', 'vega', 'vegalite', 'wavedrom']
DIAGRAM_SYNONYMNS = {'dot': 'graphviz', 'c4': 'c4plantuml'}
AVAILABLE_DIAGRAMS = DIAGRAM_TYPES + list(DIAGRAM_SYNONYMNS.keys())

# List of diagrams types the user chooses not to process
DIAGRAM_BLACKLIST = list(filter(
  lambda d: d in AVAILABLE_DIAGRAMS,
  os.environ.get('KROKI_DIAGRAM_BLACKLIST', '').split(',')
))

# kroki server to point to
KROKI_SERVER = os.environ.get('KROKI_SERVER', 'https://kroki.io/')
KROKI_SERVER = KROKI_SERVER[:-1] if KROKI_SERVER[-1] == '/' else KROKI_SERVER

def kroki(key, value, format_, _):
    if key == 'CodeBlock':
        [[ident, classes, keyvals], content] = value
        diagram_classes = list(set(AVAILABLE_DIAGRAMS) & set(classes))
        if len(diagram_classes) == 1 and diagram_classes[0] not in DIAGRAM_BLACKLIST:
            caption, typef, keyvals = get_caption(keyvals)

            # Divine the correct diagram type to use with kroki
            if diagram_classes[0] in DIAGRAM_SYNONYMNS.keys():
                diagram_type = DIAGRAM_SYNONYMNS[diagram_classes[0]]
            else:
                diagram_type = diagram_classes[0]

            # create the url to the kroki diagram and link as an image
            #content = content.replace('#scale=0.3\n','')
            d = dict()
            if '#' in content.splitlines()[0]:
                conf = content.splitlines()[0][1:]
                d = dict(conf.split("=") for x in str.split(";"))
                content = ''.join(content.splitlines(keepends=True)[1:])
            if 'scale' not in d:
                 d ['scale'] = 1.0
            encoded = base64.urlsafe_b64encode(
                zlib.compress(content.encode('utf-8'), 9)
            ).decode()
            url = f'{KROKI_SERVER}/{diagram_type}/svg/{encoded}'
            response = requests.get(url)
            # 3. Open the response into a new file called instagram.ico
            svgname = f'./img/{encoded}.svg'
            pdfname = f'./img/{encoded}.pdf'
            open(svgname, "wb").write(response.content)
            cairosvg.svg2pdf(file_obj=open(svgname, "rb"), write_to=pdfname, dpi=300, scale=float(d['scale']))

            return Para([Image([ident, [], keyvals], caption, [pdfname, typef])])
            
def main():
    toJSONFilter(kroki)

if __name__ == "__main__":
    main()
