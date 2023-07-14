import csv
import os
from pathlib import Path
from pprint import pprint
import re
import requests
from slugify import slugify
import sys
import urllib.request as urlreq

# ==== FORMAT ====
#
# Timestamp (format: M/DD/YYYY h:mm:ss) (Note: this is last updated time)
# Title
# Genre/Variant
# Author
# Image (e.g. https://drive.google.com/open?id=1MVFFavjO91c7u7izzjXxpYisVfc_WNf6)
# Description
# Rules
# Links
# Difficulty
# Category (see CATEGORIES below)

csv_filename = sys.argv[1]
source_path = Path(__file__).resolve()
source_dir = source_path.parent.as_posix()

CATEGORIES = {
    'sudoku': {
        'id': 1,
        'title': 'Sudoku and Latin Square',
    },
    'loop': {
        'id': 2,
        'title': 'Loop and Path',
    },
    'object': {
        'id': 3,
        'title': 'Object Placement',
    },
    'region': {
        'id': 4,
        'title': 'Region Division',
    },
    'shading': {
        'id': 5,
        'title': 'Shading',
    },
    'other': {
        'id': 6,
        'title': 'Others',
    },
}
CHAPTER_ORDER = ['sudoku', 'loop', 'object', 'region', 'shading', 'other']

chapter_list = [[], [], [], [], [], []]
# {
#   title: '10K Sudoku',
#   slug: '02_10k_sudoku_lavaloid',
# }

def output_latex(slug, content):
    out_filename = source_dir + '/puzzles/' + slug + '.tex'

    timestamp = row['Timestamp']
    title = row['Title']
    genre = row['Genre/Variant']
    author = row['Author']
    image = row['Image']
    description = row['Description']
    rules = row['Rules']
    links = row['Link(s)']
    difficulty = int(row['Difficulty'])
    category = row['Category']
    width = row['Width']

    # data cleanup
    title = title if title else genre
    title = title.replace('^4', '$^4$')
    title = title.replace(chr(0x2074), '$^4$')  # subscript 4
    author = author.replace('_', '\\_')
    genre = genre.title()
    genre = genre.replace('Xv', 'XV')           # ---- START genre special cases ----
    genre = genre.replace('And', 'and')
    genre = genre.replace('Jss', 'JSS')
    genre = genre.replace('Lits', 'LITS')       # ---- END genre special cases ----
    genre = re.sub(r'(\d+)X(\d+)', r'\1\\emph{x}\2', genre)
    rules = rules.replace('**Rules**\n', '')
    rules = rules.replace('\n', '\n\n')
    description = description.replace('\n', '\n\n')
    links = re.sub(r'CTC: ', 'CTC App: ', links, flags=re.IGNORECASE)
    links = links.replace('f-puzzles:', 'F-puzzles:')
    links = links.replace('F-Puzzles:', 'F-puzzles:')
    links = links.replace('PenPa+:', 'Penpa+:')
    links = links.replace('Sudokupad:', 'SudokuPad:')
    links = links.replace('puzz.link:', 'Puzz.link:')
    links = re.sub(r'puzzlink: ', 'Puzz.link: ', links, flags=re.IGNORECASE)
    links = re.sub(r'penpa: ', 'Penpa+: ', links, flags=re.IGNORECASE)

    # output
    output = ('\\section{' + title + ' | {\\normalfont ' + author + '}' '}\n'
        + '\\label{sec:' + slug + '}\n'
        + '\\puzzleinfo{' + genre + '}{' + str(difficulty/2) + '}\n'
        + description + '\n'
        + '\\puzzleimage' + (f'[{width}]' if width else '') 
                + '{./puzzle_images/' + slug + '}\n'
        
        + '\\subsection*{Rules}\n'
        + '\\begin{markdown}\n'
        + rules + '\n'
        + '\\end{markdown}\n'
        
        + '\\subsection*{Links}\n'
        + '\\begin{tabularx}{\\textwidth}{l X}\n'
    )

    for link_str in links.split('\n'):
        def print_link(name, url):
            return '\\emph{' + name + '} & \\url{' + url + '} \\\\\n'

        if ': ' in link_str:
            link_name, link = link_str.split(': ')
            output += print_link(link_name, link)
        # Check for format breaks, and automatically deduce the type of link
        elif 'f-puzzles.com' in link_str:
            output += print_link('F-puzzles', link_str)
        elif 'puzz.link' in link_str:
            output += print_link('Puzz.link', link_str)
        else:
            resp = urlreq.urlopen(link_str)
            dest = resp.url
            if 'crackingthecryptic' in dest:
                output += print_link('CTC', link_str)
            elif 'penpa-edit' in dest:
                output += print_link('Penpa+', link_str)
            elif 'puzz.link' in dest:
                output += print_link('Puzz.link', link_str)
            elif 'sudokupad' in dest:
                output += print_link('SudokuPad', link_str)
            else:
                print('ERROR: Link "' + dest + '" has no defined type')

    output += '\\end{tabularx}\n'
    output += '\\pagebreak\n'

    chapter_no = CATEGORIES[category]['id']
    chapter_list[chapter_no - 1].append({'title': title, 'slug': slug})

    with open(out_filename, 'w') as f:
        f.write(output)

def process_row(row):
    timestamp = row['Timestamp']
    title = row['Title']
    genre = row['Genre/Variant']
    author = row['Author']
    image = row['Image']
    description = row['Description']
    rules = row['Rules']
    links = row['Link(s)']
    difficulty = row['Difficulty']

    if not timestamp:
        return

    # === SLUGIFY ===
    # this is unlikely to cause collisions so i'll just leave it like this
    # unless an actual collision happens :D :D :D :D :D :D :D
    time_len = len(timestamp)
    
    combined_string = timestamp[time_len-2:time_len] + ' ' + (title if title else genre) + ' ' + author
    slug = slugify(combined_string)

    # === DOWNLOAD IMAGE ===
    # Original link: https://drive.google.com/open?id=1MVFFavjO91c7u7izzjXxpYisVfc_WNf6
    # Target link: https://drive.google.com/uc?id=1MVFFavjO91c7u7izzjXxpYisVfc_WNf6

    image_url = image.replace('open', 'uc', 1)
    dest_path = source_dir + '/puzzle_images/' + slug + '.png'

    if not os.path.isfile(dest_path):
        try:
            r = requests.get(image_url)
            with open(dest_path, 'wb') as f:
                f.write(r.content)
        except requests.exceptions.RequestException as e:
            print('ERROR fetching ' + image_url)
            print('    Slug: ' + slug)
            print('    Reason: ' + e.reason)

    output_latex(slug, row)

def process_chapter():
    for i, chapter in enumerate(chapter_list):
        chapter.sort(key=lambda p: p['title'])
        chapter_title = CATEGORIES[CHAPTER_ORDER[i]]['title']

        output = '\\chapter{' + chapter_title + '}\n'
        for puzzle in chapter:
            output += '\\input{./puzzles/' + puzzle['slug'] + '}\n'

        with open(source_dir + '/chapters/chapter0' + str(i + 1) + '.tex', 'w') as f:
            f.write(output)

with open(csv_filename) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        process_row(row)

# pprint(chapter_list)
process_chapter()
