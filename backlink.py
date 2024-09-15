from pathlib import Path 
from pprint import pprint
import re
import unicodedata
import logging

def get_all_markdown_files(path):
    p = Path(path)
    return list(p.glob('**/*.md'))

def get_all_filenames(*files):
    return [file.stem for file in files]

def simplified_string(s):
    s = remove_accents(s).decode('utf-8')
    print(s)
    return (s.casefold()
            .replace(' ', '_')
            .replace('-', '_')
            )

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii


markdown_file = get_all_markdown_files('.')
filenames = get_all_filenames(*markdown_file)
simplified_strings = [simplified_string(name) for name in filenames]
print(simplified_strings)
