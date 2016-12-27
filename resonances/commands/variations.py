from urllib.request import urlopen
from http.client import HTTPResponse
from urllib.request import URLError
from resonances.shortcuts import FAIL, ENDC
from bs4 import BeautifulSoup
from bs4.element import Tag
import traceback
import sys
from typing import Iterable
from typing import Tuple
from typing import List
from typing import Dict
import logging
import texttable
URL_BASE = 'http://newton.dm.unipi.it/neodys/index.php?pc=1.1.1&n='


def _variations_gen(from_cells: List[Tag]):
    """
    Filters td elements with variations from all.
    """
    for i, x in enumerate(from_cells):
        if (i - 2) % 3 != 0:
            continue
        yield x.get_text()


def _parse_asteroid_variations(from_html_data: str) -> Dict[str, float]:
    bs = BeautifulSoup(from_html_data, 'html.parser')
    data_table = bs.find('table', class_='simple')  # type: Tag

    if not data_table:
        raise Exception('Table doesn\'t exist')

    data_table_cells = data_table.find_all('td')
    gen = _variations_gen(data_table_cells)

    variations = {}
    for table_caption in data_table.find_all('th'):  # type: Tag
        if not table_caption.has_attr('scope'):
            continue

        variations[table_caption.get_text()] = next(gen)
    return variations


LineData = List[str]


VariationsData = Tuple[List[str], List[LineData]]


VARIATION_NAME_RESOLVE_MAP = {
    'a':           'a',
    'e':           'e',
    'i':           'i',
    'long. node':  'Ω',
    'arg. peric.': 'ω',
    'mean anomaly': 'M',
}


def grab_variations(asteroids: Iterable[str]) -> VariationsData:
    variations_name = []  # type: List[str]
    variations_data = []  # type: List[LineData]
    for asteroid_name in asteroids:
        url = '%s%s' % (URL_BASE, asteroid_name)
        try:
            logging.debug('fetch %s', asteroid_name)
            response = urlopen(url)  # type: HTTPResponse
            asteroid_html_data = response.read()
            response.close()
            variations = _parse_asteroid_variations(asteroid_html_data)
            keys = sorted(variations.keys())

            if len(keys) < 6:
                logging.warn('%s has no data on neodys' % asteroid_name)
                continue

            if not variations_name:
                variations_name.append('name')
                variations_name += [x for x in keys]

            variations_values = [variations[x] for x in keys]
            variations_data.append([asteroid_name] + variations_values)
        except URLError:
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)
            logging.warning('%sSomething wrong during fetching data from %s%s' % (FAIL, url, ENDC))

    return variations_name, variations_data


def get_variations(asteroids: Iterable[str], csv: bool):
    table = texttable.Texttable(max_width=120)
    table.set_precision(3)
    headers, data = grab_variations(asteroids)
    table.set_cols_dtype(['t']+(['e'] * len(headers)))
    if data:
        if csv:
            print(';'.join(headers))
            for line_data in data:
                print(';'.join(line_data))
        else:
            table.header(headers)
            table.add_rows(data, header=False)
            print(table.draw())
