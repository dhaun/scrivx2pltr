# scrivx2pltr - Create Plottr scene cards from an existing Scrivener file
#
# written 2021 by Dirk Haun <dirk AT haun-online DOT de>
# licensed under the MIT License
#
import argparse
import base64
import json
import os.path
import sys
import xml.etree.ElementTree as ET

### ###########################################################################
# eventually, all code handling Plottr internals should move into this class

class PlottrContent:
    """ Simple class to hold the content that goes into the Plottr file """

    #plottr_version = '2021.2.24'
    defaultColors = [ '#6cace4', '#78be20', '#e5554f', '#ff7f32', '#ffc72c', '#0b1117' ]

    def __init__(self):
        self.cards = []
        self.cardId = 1
        self.positionWithinLine = 0
        self.positionInBeat = 0

        self.beats = []
        # beatId 1 seems to have a special meaning
        self.beats.append({ 'id': 1, 'bookId': 'series', 'position': 0, 'title': 'auto', 'time': 0, 'templates': [], 'autoOutlineSort': True, 'fromTemplateId' : None })
        self.beatId = 2 # first beat for us to use
        self.positionOfBeat = 0

        self.images = {}
        self.num_images = 0


    def addCard(self, lineId, title, description):

        text = [ { 'text': description } ]
        description = [ { 'type': 'paragraph', 'children': text } ]

        card = { 'id': self.cardId, 'lineId': lineId, 'beatId': self.beatId, 'bookId': None, 'positionWithinLine': self.positionWithinLine, 'positionInBeat': self.positionInBeat, 'title': title, 'description': description, 'tags': [], 'characters': [], 'places': [], 'templates': [], 'imageId': None, 'fromTemplateId': None }

        self.cards.append(card)
        self.cardId = self.cardId + 1


    def getCards(self):
        """ Returns a list of all cards.
        This should go away once the class can write Plottr files. """

        return self.cards


    def lineOneEmpty(self):
        """ Check if we're actually using the first plotline. """

        lineOneUsed = False
        for card in self.cards:
            if card['lineId'] == 1:
                lineOneUsed = True
                break

        return not lineOneUsed


    def fixLineIdInCards(self):
        """ If the first plotline is not used, move all cards up one line. """

        for card in self.cards:
            card['lineId'] = card['lineId'] - 1


    def addBeat(self):
        self.beats.append({ 'id': self.beatId, 'bookId': 1, 'position': self.positionOfBeat, 'title': 'auto', 'time': 0, 'templates': [], 'autoOutlineSort': True, 'fromTemplateId' : None })

        self.beatId = self.beatId + 1
        self.positionOfBeat = self.positionOfBeat + 1

    def getBeats(self):
        """ Returns a list of all beats.
        This should go away once the class can write Plottr files. """

        return self.beats


    def addImageFromFile(self, file):
        """ Reads an image from a file into the proper Plottr structure.
        Returns the (internal) ID of the new image or 0 if not found. """

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
            image = { 'id': self.num_images, 'name': filename, 'path': file, 'data': data }

            self.num_images = self.num_images + 1
            self.images[str(self.num_images)] = image
            imgid = self.num_images

        return imgid
        
    def getImages(self):
        """ Returns a list of all images.
        This should go away once the class can write Plottr files. """

        return self.images


    def getColor(self, color):
        """ Return one of the 6 Plottr default colors. """

        return self.defaultColors[color % 6]

### ###########################################################################

plottr = PlottrContent()

parser = argparse.ArgumentParser(description = 'Creating a Plottr file from a Scrivener file')
parser.add_argument('scrivfile', help = 'Scrivener file to read')
parser.add_argument('-o', '--output', metavar = 'pltrfile', help = 'Plottr file to write')
parser.add_argument('--foldersAsScenes', action = 'store_true', default = False, help = 'Create scene cards for folders, too')
parser.add_argument('--flattenTimeline', action = 'store_true', default = False, help = 'Keep all scenes in one timeline')
parser.add_argument('--maxCharacters', type = int, default = -1, help = 'Max. number of Characters to read')
parser.add_argument('--maxPlaces', type = int, default = -1, help = 'Max. number of Places to read')
parser.add_argument('--charactersFolder', default = 'Characters', help = 'Name of the Characters folder, if renamed')
parser.add_argument('--placesFolder', default = 'Places', help = 'Name of the Places folder, if renamed')
args = parser.parse_args()

# sanity check Scrivener file
if args.scrivfile[-1] == '/':
    args.scrivfile = args.scrivfile[:-1]
if not os.path.isdir(args.scrivfile):
    print("ERROR: Scrivener file " + args.scrivfile + " does not exist.")
    exit(2)
scrivx = os.path.basename(args.scrivfile) + 'x'
scrivxfile = os.path.join(args.scrivfile, scrivx)
if not os.path.isfile(scrivxfile):
    print("ERROR: This does not appear to be a Scrivener 3 file.")
    exit(3)

if args.output:
    plottrfile = args.output
else:
    # if not given, create from Scrivener file name
    p = scrivx.replace('.scrivx', '.pltr')
    plottrfile = os.path.join(os.path.dirname(args.scrivfile), p)


### ###########################################################################

def write_plottrfile(plottr, filename, booktitle, characters, places):

    global lines, lineId_max

    plottr_version = '2021.2.24'

    # mostly just the default values, taken from an "empty" Plottr file
    file = { 'fileName': filename, 'loaded': True, 'dirty': False, 'version': plottr_version }
    ui = { 'currentView': 'timeline', 'currentTimeline': 1, 'timelineIsExpanded': True, 'orientation': 'horizontal', 'darkMode': False, 'characterSort': 'name~asc', 'characterFilter': None, 'placeSort': 'name-asc', 'placeFilter': None, 'noteSort': 'title-asc', 'noteFilter': None, 'timelineFilter': None, 'timelineScrollPosition': { 'x': 0, 'y': 0 }, 'timeline': { 'size': 'large' } }
    series = { 'name': booktitle, 'premise': '', 'genre': '', 'theme': '', 'templates': [] }
    books = { '1': { 'id': 1, 'title': booktitle, 'premise': '', 'genre': '', 'theme': '', 'templates': [], 'timelineTemplates': [], 'imageId': None }, 'allIds': [1] }
    categories = { 'characters': [ { 'id': 1, 'name': 'Main', 'position': 0 }, { 'id': 2, 'name': 'Supporting', 'position': 1 }, { 'id': 3, 'name': 'Other', 'position': 2 } ], 'places': [], 'notes': [], 'tags': [] }
    customAttributes = { 'characters': [], 'places': [], 'scenes': [], 'lines': [] }
    # required special plotline
    lines.append({ 'id': lineId_max + 1, 'bookId': 'series', 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None })
    notes = []
    tags = []

    fstring = '"file":' + json.dumps(file) + ','
    ustring = '"ui":' + json.dumps(ui) + ','
    sstring = '"series":' + json.dumps(series) + ','
    bstring = '"books":' + json.dumps(books) + ','
    btstring = '"beats":' + json.dumps(plottr.getBeats()) + ','
    cdstring = '"cards":' + json.dumps(plottr.getCards()) + ','
    cstring = '"categories":' + json.dumps(categories) + ','
    chstring = '"characters":' + json.dumps(characters) + ','
    custring = '"customAttributes":' + json.dumps(customAttributes) + ','
    lstring = '"lines":' + json.dumps(lines) + ','
    nstring = '"notes":' + json.dumps(notes) + ','
    pstring = '"places":' + json.dumps(places) + ','
    tstring = '"tags":' + json.dumps(tags) + ','
    istring = '"images":' + json.dumps(plottr.getImages())

    with open(filename, 'w', encoding = 'utf-8') as fs:
        fs.write('{' + fstring + ustring + sstring + bstring + btstring + cdstring + cstring + chstring + custring + lstring + nstring + pstring + tstring + istring + '}')

def read_synopsis(scrivpackage, uuid):

    syn = os.path.join(scrivpackage, 'Files', 'Data', uuid, 'synopsis.txt')
    if os.path.isfile(syn):
        with open(syn, 'r', encoding = 'utf-8') as fs:
            s = fs.read()
    else: # doesn't have a synopsis
        s = ''

    return s

def read_booktitle(scrivfile):

    booktitle = ''
    compile_xml = os.path.join(scrivfile, 'Settings/compile.xml')
    if os.path.isfile(compile_xml):
        with open(compile_xml, 'r', encoding = 'utf-8') as fs:
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

    global args, plottr

    characters = []

    if args.maxCharacters == 0:
        # we were asked not to read Characters
        return characters

    foldername = 'Characters'
    if len(args.charactersFolder) > 0:
        foldername = args.charactersFolder

    # first we need to find the Characters folder
    found = False
    for item in binder.findall('./Binder/BinderItem'):
        if item.attrib['Type'] == 'Folder':
            for child in item:
                if child.tag == 'Title' and child.text == foldername:
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
                                i = plottr.addImageFromFile(img)

                                if i > 0:
                                    ch['imageId'] = str(i)

                s = read_synopsis(scrivfile, uuid)
                if len(s) > 0:
                    ch['description'] = s

                # tbd: need to find a good solution to read RTF
                # n = read_rtf(os.path.join(content_path, 'content.rtf'))
                # if len(n) > 0:
                #     ch['notes'] = format_text(n)

                characters.append(ch)
                chId = chId + 1

                if args.maxCharacters > 0 and chId > args.maxCharacters:
                    # reached max. number of Characters to read
                    break

    return characters

def read_places(scrivfile, binder):

    global args, plottr

    places = []

    if args.maxPlaces == 0:
        # we were asked not to read Places
        return places

    foldername = 'Places'
    if len(args.placesFolder) > 0:
        foldername = args.placesFolder

    # first we need to find the Places folder
    found = False
    for item in binder.findall('./Binder/BinderItem'):
        if item.attrib['Type'] == 'Folder':
            for child in item:
                if child.tag == 'Title' and child.text == foldername:
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
                                i = plottr.addImageFromFile(img)

                                if i > 0:
                                    pl['imageId'] = str(i)

                s = read_synopsis(scrivfile, uuid)
                if len(s) > 0:
                    pl['description'] = s

                # tbd: need to find a good solution to read RTF
                # n = read_rtf(os.path.join(content_path, 'content.rtf'))
                # if len(n) > 0:
                #     pl['notes'] = format_text(n)

                places.append(pl)
                plId = plId + 1

                if args.maxPlaces > 0 and plId > args.maxPlaces:
                    # reached max. number of Places to read
                    break

    return places

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

def parse_binderitem(item):

    global args
    global beats, plottr
    global lineId, lineId_max, position_for_line
    global cardId

    if not args.flattenTimeline:
        if item.find('Children') is not None:
            lineId_last = lineId
            lineId_max = lineId_max + 1
            lineId = lineId_max
            child = item.find('Title')
            if child is None:
                plotline_title = 'Side Plot'
            else:
                plotline_title = child.text
            position_for_line = position_for_line + 1

            # add plotline
            col = plottr.getColor(lineId - 1)
            lines.append({ 'id': lineId, 'bookId': 1, 'color': col, 'title': plotline_title, 'position': position_for_line, 'characterId': None, 'expanded': None, 'fromTemplateId': None })

    if item.attrib['Type'] == 'Text' or (item.attrib['Type'] == 'Folder' and args.foldersAsScenes):
        # add this as a scene

        title = ''
        child = item.find('Title')
        if child is not None:
            title = child.text
        # for now, the Title is all we can handle (tbd: labels and such)

        s = read_synopsis(args.scrivfile, item.attrib['UUID'])

        plottr.addCard(lineId, title, s)
        # update beats
        plottr.addBeat()

    # recurse for any child items / subfolders
    if item.find('Children') is not None:
        for child in item.find('Children'):
            parse_binderitem(child)

        if not args.flattenTimeline:
            if lineId > lineId_max:
                lineId_max = lineId
            lineId = lineId_last

def remove_unusedLineOne():

    global plottr
    global lines

    # remove unused first line, move all others up
    lines.pop(0)
    for l in lines:
        l['id'] = l['id'] - 1
        l['position'] = l['position'] - 1
        l['color'] = plottr.getColor(l['id'] - 1)

    plottr.fixLineIdInCards()

### ###########################################################################


with open(scrivxfile, 'r', encoding = 'utf-8') as fs:
    sx = fs.read()

binder = ET.fromstring(sx)

# initialize Plottr data
lines = []
# default plotline
lines.append({ 'id': 1, 'bookId': 1, 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None })
lineId = 1
lineId_max = 1
position_for_line = 0


# find the Manuscript folder, aka DraftFolder
for item in binder.findall('.//BinderItem'):
    if item.attrib['Type'] == 'DraftFolder':
        manuscript = item
        break

for item in manuscript.find('Children'):
    parse_binderitem(item)

# if each folder gets its own plotline, check if line 1 has any cards on it
if not args.flattenTimeline:
    if plottr.lineOneEmpty():
        remove_unusedLineOne()

booktitle = read_booktitle(args.scrivfile)
characters = read_characters(args.scrivfile, binder)
places = read_places(args.scrivfile, binder)
write_plottrfile(plottr, plottrfile, booktitle, characters, places)

