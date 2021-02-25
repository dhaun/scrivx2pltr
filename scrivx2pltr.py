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

def write_plottrfile(filename, cards, beats):

    bstring = '"beats":' + json.dumps(beats)
    cstring = '"cards":' + json.dumps(cards)

    file = { 'fileName': filename, 'loaded': True, 'dirty': False, 'version': '2021.2.19' }
    fstring = '"file":' + json.dumps(file)

    with open(filename, 'w') as fs:
        fs.write("# Note: This is not a complete Plottr file (yet)!\n")
        fs.write('{' + fstring)
        fs.write(bstring)
        fs.write(cstring)
        fs.write('}')

def read_synopsis(scrivpackage, uuid):

    syn = scrivpackage + '/Files/Data/' + uuid + '/synopsis.txt'
    if os.path.isfile(syn):
        fs = open(syn, 'r')
        s = fs.read()
        fs.close()
    else: # doesn't have a synopsis
        s = ''

    return s

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
beatId = 3

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

write_plottrfile(plottrfile, cards, beats)
