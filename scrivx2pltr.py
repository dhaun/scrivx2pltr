# scrivx2pltr - Create Plottr scene cards from an existing Scrivener file
#
# written by Dirk Haun <dirk AT haun-online DOT de>
# licensed under the MIT License
#
import base64
import json
import os.path
import sys
import xml.etree.ElementTree as ET

# global variables
images = {}
num_images = 0

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

def write_plottrfile(filename, booktitle, cards, beats, characters, places):

    global images

    plottr_version = '2021.2.19'

    # mostly just the default values, taken from an "empty" Plottr file
    file = { 'fileName': filename, 'loaded': True, 'dirty': False, 'version': plottr_version }
    ui = { 'currentView': 'timeline', 'currentTimeline': 1, 'timelineIsExpanded': True, 'orientation': 'horizontal', 'darkMode': False, 'characterSort': 'name~asc', 'characterFilter': None, 'placeSort': 'name-asc', 'placeFilter': None, 'noteSort': 'title-asc', 'noteFilter': None, 'timelineFilter': None, 'timelineScrollPosition': { 'x': 0, 'y': 0 }, 'timeline': { 'size': 'large' } }
    series = { 'name': booktitle, 'premise': '', 'genre': '', 'theme': '', 'templates': [] }
    books = { '1': { 'id': 1, 'title': booktitle, 'premise': '', 'genre': '', 'theme': '', 'templates': [], 'timelineTemplates': [], 'imageId': None }, 'allIds': [1] }
    categories = { 'characters': [ { 'id': 1, 'name': 'Main', 'position': 0 }, { 'id': 2, 'name': 'Supporting', 'position': 1 }, { 'id': 3, 'name': 'Other', 'position': 2 } ], 'places': [], 'notes': [], 'tags': [] }
    customAttributes = { 'characters': [], 'places': [], 'scenes': [], 'lines': [] }
    lines = [ { 'id': 1, 'bookId': 1, 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None }, { 'id': 2, 'bookId': 'series', 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None } ]
    notes = []
    tags = []

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

def read_characters(scrivfile, binder):

    characters = []

    # first we need to find the Characters folder
    found = False
    for item in binder.findall('./Binder/BinderItem'):
        if item.attrib['Type'] == 'Folder':
            for child in item:
                if child.tag == 'Title' and child.text == 'Characters':
                    found = True
                    break
            if found:
                break

    if found:
        chId = 1
        files_data = os.path.join(scrivfile, 'Files', 'Data')

        for char in item.findall('.//BinderItem'):
            ch = { 'id': 1, 'name': '', 'description': '', 'notes': [], 'color': None, 'cards': [], 'noteIds': [], 'templates': [], 'tags': [], 'categoryId': '1', 'imageId': '', 'bookIds': [1] }

            if char.attrib['Type'] == 'Text':
                uuid = char.attrib['UUID']
                content_path = os.path.join(files_data, uuid)
                for child in char:
                    if child.tag == 'Title':
                        ch['id'] = chId
                        ch['name'] = child.text
                    elif child.tag == 'MetaData':
                        ext = child.find('.//IndexCardImageFileExtension')
                        if ext is not None:
                            if len(ext.text) > 0:
                                imgname = 'card-image.' + ext.text
                                img = os.path.join(content_path, imgname)
                                i = read_image(img)

                                if i > 0:
                                    ch['imageId'] = str(i)

                # tbd: need to find a good solution to read RTF
                # n = read_rtf(os.path.join(content_path, 'content.rtf'))
                # if len(n) > 0:
                #     ch['notes'] = format_text(n)

                characters.append(ch)
                chId = chId + 1

    return characters

def read_places(scrivfile, binder):

    places = []

    # first we need to find the Places folder
    found = False
    for item in binder.findall('./Binder/BinderItem'):
        if item.attrib['Type'] == 'Folder':
            for child in item:
                if child.tag == 'Title' and child.text == 'Places':
                    found = True
                    break
            if found:
                break

    if found:
        plId = 1
        files_data = os.path.join(scrivfile, 'Files', 'Data')

        for place in item.findall('.//BinderItem'):
            pl = { 'id': 1, 'name': '', 'description': '', 'notes': [], 'color': None, 'cards': [], 'noteIds': [], 'templates': [], 'tags': [], 'imageId': '', 'bookIds': [1] }

            if place.attrib['Type'] == 'Text':
                uuid = place.attrib['UUID']
                content_path = os.path.join(files_data, uuid)
                for child in place:
                    if child.tag == 'Title':
                        pl['id'] = plId
                        pl['name'] = child.text
                    elif child.tag == 'MetaData':
                        ext = child.find('.//IndexCardImageFileExtension')
                        if ext is not None:
                            if len(ext.text) > 0:
                                imgname = 'card-image.' + ext.text
                                img = os.path.join(content_path, imgname)
                                i = read_image(img)

                                if i > 0:
                                    pl['imageId'] = str(i)

                # tbd: need to find a good solution to read RTF
                # n = read_rtf(os.path.join(content_path, 'content.rtf'))
                # if len(n) > 0:
                #     pl['notes'] = format_text(n)

                places.append(pl)
                plId = plId + 1

    return places

# reads an image into the global(!) images list
def read_image(file):

    global images, num_images

    imgid = 0

    if os.path.isfile(file):
        with open(file, 'rb') as fs:
            imgdata = fs.read() 

        ibdata = base64.b64encode(imgdata)
        ibstring = ibdata.decode('utf-8')

        filename = os.path.basename(file)
        x = filename.split('.')
        ext = x[-1]

        if ext == 'jpg' or ext == 'jpeg':
            imgtype = 'jpeg'
        elif ext == 'png':
            imgtype = 'png'
        elif ext == 'gif':
            imgtype = 'gif'
        else: # what other image types could there be?
            imgtype = 'unknown'
        data = 'data:image/' + imgtype + ';base64,' + ibstring
        i = { 'id': num_images, 'name': filename, 'path': file, 'data': data }

        num_images = num_images + 1
        images[str(num_images)] = i
        imgid = num_images

    return imgid

def read_rtf(file):

    r = ''
    if os.path.isfile(file):
        with open(file, 'r') as fs:
            rtf = fs.read() 
    r = rtf

    return r

def format_text(text):

    f = []

    if len(text) > 0:
        f.append( { 'children': [ { 'text': text } ] })

    return f

### ###########################################################################


with open(scrivxfile, 'r') as fs:
    sx = fs.read()

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

# find the Manuscript folder (might be renamed)
for item in binder.findall('.//BinderItem'):
    if item.attrib['Type'] == 'DraftFolder':
        manuscript = item
        break

# now iterating over all Binder items in the Manuscript folder
for item in manuscript.findall('.//BinderItem'):

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
characters = read_characters(scrivfile, binder)
places = read_places(scrivfile, binder)
write_plottrfile(plottrfile, booktitle, cards, beats, characters, places)

