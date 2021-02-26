# scrivx2pltr - Create Plottr scene cards from an existing Scrivener file
#
# written by Dirk Haun <dirk AT haun-online DOT de>
# licensed under the MIT License
#
import json
import os.path
import sys
import xml.etree.ElementTree as ET

args = len(sys.argv)
if args == 1:
    print("usage: " + sys.argv[0] + " <scrivener-file> [<plottr-file>]")
    exit(1)

# first parameter is the Scrivener file
if args >= 2:
    scrivfile = sys.argv[1]
    # Scrivener files are actually directories (on a Mac)
    if not os.path.isdir(scrivfile):
        print("ERROR: Scrivener file " + scrivfile + " does not exist.")
        exit(2)

scrivx = os.path.basename(scrivfile) + 'x'
scrivxfile = os.path.join(scrivfile, scrivx)
if not os.path.isfile(scrivxfile):
    print("ERROR: This does not appear to be a Scrivener 3 file.")
    exit(3)

# second (optional) argument is the output file
if args >= 3:
    plottrfile = sys.argv[2]
else:
    # if not given, create from Scrivener file name
    p = scrivx.replace('.scrivx', '.pltr')
    plottrfile = os.path.join(os.path.dirname(scrivfile), p)

# any other arguments ignored (for now)


### ###########################################################################

def write_plottrfile(filename, booktitle, cards, beats):

    plottr_version = '2021.2.19'

    # mostly just the default values, taken from an "empty" Plottr file
    file = { 'fileName': filename, 'loaded': True, 'dirty': False, 'version': plottr_version }
    ui = { 'currentView': 'timeline', 'currentTimeline': 1, 'timelineIsExpanded': True, 'orientation': 'horizontal', 'darkMode': False, 'characterSort': 'name~asc', 'characterFilter': None, 'placeSort': 'name-asc', 'placeFilter': None, 'noteSort': 'title-asc', 'noteFilter': None, 'timelineFilter': None, 'timelineScrollPosition': { 'x': 0, 'y': 0 }, 'timeline': { 'size': 'large' } }
    series = { 'name': booktitle, 'premise': '', 'genre': '', 'theme': '', 'templates': [] }
    books = { '1': { 'id': 1, 'title': booktitle, 'premise': '', 'genre': '', 'theme': '', 'templates': [], 'timelineTemplates': [], 'imageId': None }, 'allIds': [1] }
    categories = { 'characters': [ { 'id': 1, 'name': 'Main', 'position': 0 }, { 'id': 2, 'name': 'Supporting', 'position': 1 }, { 'id': 3, 'name': 'Other', 'position': 2 } ], 'places': [], 'notes': [], 'tags': [] }
    characters = [] # hope to fill these in later
    customAttributes = { 'characters': [], 'places': [], 'scenes': [], 'lines': [] }
    lines = [ { 'id': 1, 'bookId': 1, 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None }, { 'id': 2, 'bookId': 'series', 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None } ]
    notes = []
    places = []
    tags = []
    images = {}

    fstring = '"file":' + json.dumps(file) + ','
    ustring = '"ui":' + json.dumps(ui) + ','
    sstring = '"series":' + json.dumps(series) + ','
    bstring = '"books":' + json.dumps(books) + ','
    btstring = '"beats":' + json.dumps(beats) + ','
    cdstring = '"cards":' + json.dumps(cards) + ','
    cstring = '"categories":' + json.dumps(categories) + ','
    chstring = '"characters":' + json.dumps(characters) + ','
    custring = '"customAttributes":' + json.dumps(customAttributes) + ','
    lstring = '"lines":' + json.dumps(lines) + ','
    nstring = '"notes":' + json.dumps(notes) + ','
    pstring = '"places":' + json.dumps(places) + ','
    tstring = '"tags":' + json.dumps(tags) + ','
    istring = '"images":' + json.dumps(images)

    with open(filename, 'w') as fs:
        fs.write('{' + fstring + ustring + sstring + bstring + btstring + cdstring + cstring + chstring + custring + lstring + nstring + pstring + tstring + istring + '}')

def read_synopsis(scrivpackage, uuid):

    syn = scrivpackage + '/Files/Data/' + uuid + '/synopsis.txt'
    if os.path.isfile(syn):
        fs = open(syn, 'r')
        s = fs.read()
        fs.close()
    else: # doesn't have a synopsis
        s = ''

    return s

def read_booktitle(scrivfile):

    booktitle = ''
    compile_xml = os.path.join(scrivfile, 'Settings/compile.xml')
    if os.path.isfile(compile_xml):
        with open(compile_xml, 'r') as fs:
            xmlstring = fs.read()
            cxml = ET.fromstring(xmlstring)
            item = cxml.find('.//ProjectTitle')
            if item is not None:
                booktitle = item.text

    # fallback: use file name
    if len(booktitle) == 0:
        b = os.path.basename(scrivfile)
        booktitle = b.replace('.scriv', '')

    return booktitle

### ###########################################################################


# tbd: error handling (we did check it exists, though)
sf = open(scrivxfile, 'r')
sx = sf.read()
sf.close()

binder = ET.fromstring(sx)

# initialize Plottr data
cards = []
cardId = 1
lineId = 1
position = 1
bookId = None
positionWithinLine = 0
positionInBeat = 0

beats = []
# beatId 1 + 2 seem to have special meaning
beats.append({ 'id': 1, 'bookId': 'series', 'position': 0, 'title': 'auto', 'time': 0, 'templates': [], 'autoOutlineSort': True, 'fromTemplateId' : None })
beats.append({ 'id': 2, 'bookId': 1, 'position': 0, 'title': 'auto', 'time': 0, 'templates': [], 'autoOutlineSort': True, 'fromTemplateId' : None })
beatId = 2

# first Binder item is the Manuscript folder (might be renamed)
root = binder.find('.//BinderItem')

# now iterating over all Binder items in the Manuscript folder
for item in root.findall('.//BinderItem'):

    # tbd: handling folders - option to include?
    if item.attrib['Type'] == 'Folder':
        continue

    for child in item:
        if child.tag == 'Title':
            title = child.text
            # for now, that's all we need (tbd: labels and such)
            break

    s = read_synopsis(scrivfile, item.attrib['UUID'])

    card = {}
    card['id'] = cardId
    card['lineId'] = lineId
    card['beatId'] = beatId
    card['bookId'] = bookId
    card['positionWithinLine'] = positionWithinLine
    card['positionInBeat'] = positionInBeat
    card['title'] = title
    desc = {}
    desc['type'] = 'paragraph'
    txt = {}
    txt['text'] = s
    desc['children'] = [ txt ]
    card['description'] = [ desc ]
    card['tags'] = []
    card['characters'] = []
    card['places'] = []
    card['templates'] = []
    card['imageId'] = None
    card['fromTemplateId'] = None

    cards.append(card)
    cardId = cardId + 1

    # update beats
    beats.append({ 'id': beatId, 'bookId': 1, 'position': position, 'title': 'auto', 'time': 0, 'templates': [], 'autoOutlineSort': True, 'fromTemplateId' : None })

    beatId = beatId + 1
    position = position + 1

booktitle = read_booktitle(scrivfile)
write_plottrfile(plottrfile, booktitle, cards, beats)
