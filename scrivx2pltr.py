# scrivx2pltr - Creates a Plottr file from a Scrivener 3 project
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

#from striprtf import rtf_to_text

### ###########################################################################

class PlottrContent:
    """ Simple class to hold the content that goes into the Plottr file """

    plottr_version = '2021.2.24'
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

        self.characters = []
        self.characterId = 1

        self.places = []
        self.placeId = 1

        self.lines = []
        # default plotline
        self.lines.append({ 'id': 1, 'bookId': 1, 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None })
        self.lineId = 1
        self.lineId_max = 1
        self.position_for_line = 0

        self.booktitle = ''
        self.premise = ''

        self.labels = {}
        self.keywords = {}
        self.tagId = 0

        self.config = {}
        self.config['useLabelColorsForSceneCards'] = False
        self.config['labelsAreCharacters'] = False
        self.config['keywordsAreCharacters'] = False
        self.config['keywordsAreTags'] = False


    def __getColor(self, color):
        """ Return one of the 6 Plottr default colors. """

        return self.defaultColors[color % 6]


    def __addImageFromFile(self, file):
        """ Reads an image from a file into the proper Plottr structure.
        Returns the (internal) ID of the new image or -1 if not found. """

        imgid = -1

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

            # most filenames are actually just "card-image.jpg"
            # use the uniq id of the directory to create a unique filename
            d = os.path.dirname(file)
            filename = os.path.basename(d) + '.' + ext

            imgid = self.num_images
            image = { 'id': imgid, 'name': filename, 'path': file, 'data': data }

            self.images[str(imgid)] = image
            self.num_images = self.num_images + 1

        return imgid


    def __addBeat(self):
        self.beats.append({ 'id': self.beatId, 'bookId': 1, 'position': self.positionOfBeat, 'title': 'auto', 'time': 0, 'templates': [], 'autoOutlineSort': True, 'fromTemplateId' : None })

        self.beatId = self.beatId + 1
        self.positionOfBeat = self.positionOfBeat + 1


    def setBookTitle(self, title):
        self.booktitle = title


    def setPremise(self, premise):
        self.premise = premise


    def useLabelColors(self, useLabelColors):
        self.config['useLabelColorsForSceneCards'] = useLabelColors


    def labelsAreCharacters(self, labelsAreCharacters):
        self.config['labelsAreCharacters'] = labelsAreCharacters


    def keywordsAreCharacters(self, keywordsAreCharacters):
        self.config['keywordsAreCharacters'] = keywordsAreCharacters


    def keywordsAreTags(self, keywordsAreTags):
        self.config['keywordsAreTags'] = keywordsAreTags


    def addLabel(self, id, title, color):
        self.labels[id] = { 'title': title, 'color': color }


    def addKeyword(self, id, title, color):
        if self.config['keywordsAreTags']:
            self.tagId = self.tagId + 1
        self.keywords[id] = { 'title': title, 'color': color, 'tagId': self.tagId }


    def __matchLabelToCharacter(self, label):

        characters = []

        l = self.labels.get(label)
        if l is not None:
            for ch in self.characters:
                if ch['name'] == l['title']:
                    characters.append(ch['id'])
                    break

        return characters


    def __matchKeywordsToCharacters(self, keywords, characters):
        """ See if we can match any Scrivener keywords with character names.
            Should run after __matchLabelToCharacter(). """

        for k in keywords:
            kch = self.keywords.get(k)
            if kch is not None:
                # found the keyword, now find it in the list of characters
                for ch in self.characters:
                    if ch['name'] == kch['title']:
                        if not ch['id'] in characters:
                            characters.append(ch['id'])
                        break

        return characters


    def __matchKeywordsToTags(self, keywords):

        tags = []
        for k in keywords:
            ktg = self.keywords.get(k)
            if ktg is not None:
                if ktg['tagId'] > 0:
                    tags.append(ktg['tagId'])

        return tags


    def addCard(self, title, description, label = '', keywords = []):

        text = [ { 'text': description } ]
        description = [ { 'type': 'paragraph', 'children': text } ]

        card = { 'id': self.cardId, 'lineId': self.lineId, 'beatId': self.beatId, 'bookId': None, 'positionWithinLine': self.positionWithinLine, 'positionInBeat': self.positionInBeat, 'title': title, 'description': description, 'tags': [], 'characters': [], 'places': [], 'templates': [], 'imageId': None, 'fromTemplateId': None, 'color': None }

        if self.config['useLabelColorsForSceneCards'] and len(label) > 0:
            l = self.labels.get(label)
            if l is not None:
                card['color'] = l['color']

        if self.config['labelsAreCharacters'] and len(label) > 0:
            card['characters'] = self.__matchLabelToCharacter(label)

        if self.config['keywordsAreCharacters'] and len(keywords) > 0:
            card['characters'] = self.__matchKeywordsToCharacters(keywords, card['characters'])

        if self.config['keywordsAreTags'] and len(keywords) > 0:
            card['tags'] = self.__matchKeywordsToTags(keywords)

        self.cards.append(card)
        self.cardId = self.cardId + 1

        # update beats
        self.__addBeat()


    def addCharacter(self, name, description, imagefile, notes = '', keywords = []):

        imageId = self.__addImageFromFile(imagefile)
        if imageId >= 0:
            image = str(imageId)
        else:
            image = ''

        if len(notes) > 0:
            n = [ { 'children': [ { 'text': notes } ] } ]
        else:
            n = []

        ch = { 'id': self.characterId, 'name': name, 'description': description, 'notes': n, 'color': None, 'cards': [], 'noteIds': [], 'templates': [], 'tags': [], 'categoryId': '1', 'imageId': image, 'bookIds': [1] }

        if self.config['keywordsAreTags'] and len(keywords) > 0:
            ch['tags'] = self.__matchKeywordsToTags(keywords)

        self.characters.append(ch)
        self.characterId = self.characterId + 1


    def addPlace(self, name, description, imagefile, notes = '', keywords = ''):

        imageId = self.__addImageFromFile(imagefile)
        if imageId >= 0:
            image = str(imageId)
        else:
            image = ''

        if len(notes) > 0:
            n = [ { 'children': [ { 'text': notes } ] } ]
        else:
            n = []

        pl = { 'id': self.placeId, 'name': name, 'description': description, 'notes': n, 'color': None, 'cards': [], 'noteIds': [], 'templates': [], 'tags': [], 'imageId': image, 'bookIds': [1] }

        if self.config['keywordsAreTags'] and len(keywords) > 0:
            pl['tags'] = self.__matchKeywordsToTags(keywords)

        self.places.append(pl)
        self.placeId = self.placeId + 1


    def newPlotline(self, title):
        """ Start a new plotline. """

        state = self.lineId
        self.lineId_max = self.lineId_max + 1
        self.lineId = self.lineId_max
        self.position_for_line = self.position_for_line + 1

        col = self.__getColor(self.lineId - 1)
        self.lines.append({ 'id': self.lineId, 'bookId': 1, 'color': col, 'title': title, 'position': self.position_for_line, 'characterId': None, 'expanded': None, 'fromTemplateId': None })

        # return an unexplained "state" to the caller for use in recursion
        return state


    def __plotlineEmpty(self):
        """ Check if the current plotline is empty, ie. has no cards on it """

        lineUsed = False
        for card in self.cards:
            if card['lineId'] == self.lineId:
                lineUsed = True
                break

        return not lineUsed


    def closePlotline(self, state):
        """ Close current plotline and return to the previous one. """

        if self.__plotlineEmpty():
            # current plotline is empty - remove it and move the others up by 1
            self.lines.pop(self.lineId - 1)
            for l in self.lines:
                if l['id'] > self.lineId:
                    l['id'] = l['id'] - 1
                    l['position'] = l['position'] - 1
                    l['color'] = self.__getColor(l['id'] - 1)

            for card in self.cards:
                if card['lineId'] > self.lineId:
                    card['lineId'] = card['lineId'] - 1

            # adjust counters
            if self.lineId_max > self.lineId:
                self.lineId_max = self.lineId_max - 1
            if state > self.lineId:
                state = state - 1
            self.lineId = self.lineId - 1

        if self.lineId > self.lineId_max:
            self.lineId_max = self.lineId
        self.lineId = state # "state" is really just the last lineId (for now)


    def __finalisePlotlines(self):

        self.closePlotline(0) # explicitly close the default plotline

        # required special plotline
        self.lines.append({ 'id': self.lineId_max + 1, 'bookId': 'series', 'color': '#6cace4', 'title': 'Main Plot', 'position': 0, 'characterId': None, 'expanded': None, 'fromTemplateId': None })


    def write(self, filename):

        self.__finalisePlotlines()

        # mostly just the default values, taken from an "empty" Plottr file
        file = { 'fileName': filename, 'loaded': True, 'dirty': False, 'version': self.plottr_version }
        ui = { 'currentView': 'timeline', 'currentTimeline': 1, 'timelineIsExpanded': True, 'orientation': 'horizontal', 'darkMode': False, 'characterSort': 'name~asc', 'characterFilter': None, 'placeSort': 'name-asc', 'placeFilter': None, 'noteSort': 'title-asc', 'noteFilter': None, 'timelineFilter': None, 'timelineScrollPosition': { 'x': 0, 'y': 0 }, 'timeline': { 'size': 'large' } }
        series = { 'name': self.booktitle, 'premise': self.premise, 'genre': '', 'theme': '', 'templates': [] }
        books = { '1': { 'id': 1, 'title': self.booktitle, 'premise': self.premise, 'genre': '', 'theme': '', 'templates': [], 'timelineTemplates': [], 'imageId': None }, 'allIds': [1] }
        categories = { 'characters': [ { 'id': 1, 'name': 'Main', 'position': 0 }, { 'id': 2, 'name': 'Supporting', 'position': 1 }, { 'id': 3, 'name': 'Other', 'position': 2 } ], 'places': [], 'notes': [], 'tags': [] }
        customAttributes = { 'characters': [], 'places': [], 'scenes': [], 'lines': [] }
        notes = []

        tags = []
        if self.config['keywordsAreTags'] and self.tagId > 0:
            for k in self.keywords:
                t = self.keywords[k]
                tags.append({'id': t['tagId'], 'title': t['title'], 'color': t['color']})

        fstring = '"file":' + json.dumps(file) + ','
        ustring = '"ui":' + json.dumps(ui) + ','
        sstring = '"series":' + json.dumps(series) + ','
        bstring = '"books":' + json.dumps(books) + ','
        btstring = '"beats":' + json.dumps(self.beats) + ','
        cdstring = '"cards":' + json.dumps(self.cards) + ','
        cstring = '"categories":' + json.dumps(categories) + ','
        chstring = '"characters":' + json.dumps(self.characters) + ','
        custring = '"customAttributes":' + json.dumps(customAttributes) + ','
        lstring = '"lines":' + json.dumps(self.lines) + ','
        nstring = '"notes":' + json.dumps(notes) + ','
        pstring = '"places":' + json.dumps(self.places) + ','
        tstring = '"tags":' + json.dumps(tags) + ','
        istring = '"images":' + json.dumps(self.images)

        with open(filename, 'w', encoding = 'utf-8') as fs:
            fs.write('{' + fstring + ustring + sstring + bstring + btstring + cdstring + cstring + chstring + custring + lstring + nstring + pstring + tstring + istring + '}')

### ###########################################################################

def read_synopsis(scrivpackage, uuid):

    syn = os.path.join(scrivpackage, 'Files', 'Data', uuid, 'synopsis.txt')
    if os.path.isfile(syn):
        with open(syn, 'r', encoding = 'utf-8') as fs:
            s = fs.read()
    else: # doesn't have a synopsis
        s = ''

    return s

def read_notes(scrivpackage, uuid):

    n = ''

    #syn = os.path.join(scrivpackage, 'Files', 'Data', uuid, 'notes.rtf')
    #if os.path.isfile(syn):
    #    with open(syn, 'r', encoding = 'utf-8') as fs:
    #        n = fs.read()
    #    if len(n) > 0:
    #        n = rtf_to_text(n)

    return n

def read_bookinfo(scrivfile):

    global plottr

    booktitle = ''
    premise = ''

    compile_xml = os.path.join(scrivfile, 'Settings', 'compile.xml')
    if os.path.isfile(compile_xml):
        with open(compile_xml, 'r', encoding = 'utf-8') as fs:
            xmlstring = fs.read()

        cxml = ET.fromstring(xmlstring)
        item = cxml.find('.//ProjectTitle')
        if item is not None:
            booktitle = item.text
        item = cxml.find('.//EbookDescription')
        if item is not None:
            premise = item.text

    # fallback: use file name as book title
    if len(booktitle) == 0:
        b = os.path.basename(scrivfile)
        booktitle = b.replace('.scriv', '')

    plottr.setBookTitle(booktitle)
    plottr.setPremise(premise)


def get_keywords(item):
    """ Get any keywords attached to an item (scene, character, place, ...) """

    keywords = []
    child = item.find('./Keywords')
    if child is not None:
        for k in child.findall('KeywordID'):
            keywords.append(k.text)

    return keywords


def read_characters(scrivfile, scrivp):

    global args, plottr

    if args.maxCharacters == 0:
        # we were asked not to read Characters
        return

    foldername = 'Characters'
    if len(args.charactersFolder) > 0:
        foldername = args.charactersFolder

    # first we need to find the Characters folder
    found = False
    for item in scrivp.findall('./Binder/BinderItem'):
        if item.attrib['Type'] == 'Folder':
            for child in item:
                if child.tag == 'Title' and child.text == foldername:
                    found = True
                    break
            if found:
                break

    if found:
        files_data = os.path.join(scrivfile, 'Files', 'Data')

        characters_read = 0
        for char in item.findall('.//BinderItem'):

            character_name = ''
            character_desc = ''
            character_notes = ''
            character_image = ''
            if char.attrib['Type'] == 'Text':
                uuid = char.attrib['UUID']
                content_path = os.path.join(files_data, uuid)
                for child in char:
                    if child.tag == 'Title':
                        character_name = child.text
                    elif child.tag == 'MetaData':
                        ext = child.find('.//IndexCardImageFileExtension')
                        if ext is not None:
                            if len(ext.text) > 0:
                                imgname = 'card-image.' + ext.text
                                character_image = os.path.join(content_path, imgname)

                s = read_synopsis(scrivfile, uuid)
                if len(s) > 0:
                    character_desc = s

                n = read_notes(scrivfile, uuid)
                if len(n) > 0:
                    character_notes = n

                keywords = get_keywords(char)

                plottr.addCharacter(character_name, character_desc, character_image, character_notes, keywords)
                characters_read = characters_read + 1

                if args.maxCharacters > 0 and characters_read == args.maxCharacters:
                    # reached max. number of Characters to read
                    break


def read_places(scrivfile, scrivp):

    global args, plottr

    if args.maxPlaces == 0:
        # we were asked not to read Places
        return

    foldername = 'Places'
    if len(args.placesFolder) > 0:
        foldername = args.placesFolder

    # first we need to find the Places folder
    found = False
    for item in scrivp.findall('./Binder/BinderItem'):
        if item.attrib['Type'] == 'Folder':
            for child in item:
                if child.tag == 'Title' and child.text == foldername:
                    found = True
                    break
            if found:
                break

    if found:
        files_data = os.path.join(scrivfile, 'Files', 'Data')

        places_read = 0
        for place in item.findall('.//BinderItem'):

            place_name = ''
            place_desc = ''
            place_notes = ''
            place_image = ''
            if place.attrib['Type'] == 'Text':
                uuid = place.attrib['UUID']
                content_path = os.path.join(files_data, uuid)
                for child in place:
                    if child.tag == 'Title':
                        place_name = child.text
                    elif child.tag == 'MetaData':
                        ext = child.find('.//IndexCardImageFileExtension')
                        if ext is not None:
                            if len(ext.text) > 0:
                                imgname = 'card-image.' + ext.text
                                place_image = os.path.join(content_path, imgname)

                s = read_synopsis(scrivfile, uuid)
                if len(s) > 0:
                    place_desc = s

                n = read_notes(scrivfile, uuid)
                if len(n) > 0:
                    place_notes = n

                keywords = get_keywords(place)

                plottr.addPlace(place_name, place_desc, place_image, place_notes, keywords)
                places_read = places_read + 1

                if args.maxPlaces > 0 and places_read == args.maxPlaces:
                    # reached max. number of Places to read
                    break


def parse_binderitem(item):

    global args, plottr

    if not args.flattenTimeline:
        if item.find('Children') is not None:
            child = item.find('Title')
            if child is None:
                plotline_title = 'Side Plot'
            else:
                plotline_title = child.text

            # add plotline
            state = plottr.newPlotline(plotline_title)

    if item.attrib['Type'] == 'Text' or (item.attrib['Type'] == 'Folder' and args.foldersAsScenes):

        # add this as a scene
        title = ''
        child = item.find('Title')
        if child is not None:
            title = child.text

        label = ''
        child = item.find('./MetaData/LabelID')
        if child is not None:
            label = child.text

        keywords = get_keywords(item)

        s = read_synopsis(args.scrivfile, item.attrib['UUID'])

        plottr.addCard(title, s, label, keywords)

    # recurse for any child items / subfolders
    if item.find('Children') is not None:
        for child in item.find('Children'):
            parse_binderitem(child)

        if not args.flattenTimeline:
            plottr.closePlotline(state)

def color_to_hex(scrivcolor):
    """ Scrivener stores colours as 3 float values,
        Plottr prefers 6-digit hex strings. So convert. """

    h = '#'
    values = scrivcolor.split()
    for v in values:
        h = h + '{:02x}'.format(round(float(v) * 255))

    return h

def read_labels(scrivp):

    labelsettings = scrivp.find('./LabelSettings')
    if labelsettings is not None:
        defId = '-1'
        for child in labelsettings:
            if child.tag == 'DefaultLabelID':
                defId = child.text
            elif child.tag == 'Labels':
                for label in child.findall('./Label'):
                    if label.attrib['ID'] == defId:
                        continue
                    else:
                        plottr.addLabel(label.attrib['ID'], label.text, color_to_hex(label.attrib['Color']))
                break

def read_keywords(scrivp):
    """ Read all Scrivener keywords (which can be nested) into a flat list. """

    keywords = scrivp.find('./Keywords')
    if keywords is not None:
        keys = keywords.findall('.//Keyword')
        if keys is not None:
            for k in keys:
                keyId = k.attrib['ID']
                title = ''
                tg = k.find('Title')
                if tg is not None:
                    title = tg.text
                col = ''
                cl = k.find('Color')
                if cl is not None:
                    color = color_to_hex(cl.text)

                if len(title) > 0 and len(color) > 0:
                    plottr.addKeyword(keyId, title, color)


### ###########################################################################

parser = argparse.ArgumentParser(description = 'Creating a Plottr file from a Scrivener file')
parser.add_argument('scrivfile', help = 'Scrivener file to read')
parser.add_argument('-o', '--output', metavar = 'pltrfile', help = 'Plottr file to write')
parser.add_argument('--foldersAsScenes', action = 'store_true', default = False, help = 'Create scene cards for folders, too')
parser.add_argument('--flattenTimeline', action = 'store_true', default = False, help = 'Keep all scenes in one timeline')
parser.add_argument('--useLabelColors', action = 'store_true', default = False, help = 'Use the Scrivener label colors for the scene cards')
parser.add_argument('--labelsAreCharacters', action = 'store_true', default = False, help = 'Match Scrivener labels to characters')
parser.add_argument('--keywordsAreCharacters', action = 'store_true', default = False, help = 'Match Scrivener keywords to characters')
parser.add_argument('--keywordsAreTags', action = 'store_true', default = False, help = 'Treat Scrivener keywords as Plottr tags')
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

# name of the .scrivx file may differ from the .scriv
scrivx = ''
with os.scandir(args.scrivfile) as it:
    for entry in it:
        if entry.name.endswith('.scrivx'):
            scrivx = entry.name
            break
if len(scrivx) == 0: # last-ditch effort ...
    scrivx = os.path.basename(args.scrivfile) + 'x'

scrivxfile = os.path.join(args.scrivfile, scrivx)
if not os.path.isfile(scrivxfile):
    print("ERROR: This does not appear to be a Scrivener file.")
    exit(3)

if args.output:
    if os.path.isdir(args.output):
        p = scrivx.replace('.scrivx', '.pltr')
        plottrfile = os.path.join(args.output, p)
    else:
        plottrfile = args.output
else:
    # if not given, create from Scrivener file name
    p = scrivx.replace('.scrivx', '.pltr')
    plottrfile = os.path.join(os.path.dirname(args.scrivfile), p)

with open(scrivxfile, 'r', encoding = 'utf-8') as fs:
    sx = fs.read()

scrivp = ET.fromstring(sx)

# final Scrivener sanity check: is it a Scrivener 3 file (XML version 2.0)?
if scrivp.attrib['Version'] != '2.0':
    print("ERROR: This does not appear to be a Scrivener 3 file.")
    exit(4)

# all fine, let's go

plottr = PlottrContent()

plottr.useLabelColors(args.useLabelColors)
plottr.labelsAreCharacters(args.labelsAreCharacters)
plottr.keywordsAreCharacters(args.keywordsAreCharacters)
plottr.keywordsAreTags(args.keywordsAreTags)

# find the Manuscript folder, aka DraftFolder
for item in scrivp.findall('.//BinderItem'):
    if item.attrib['Type'] == 'DraftFolder':
        manuscript = item
        break

read_labels(scrivp)
read_keywords(scrivp)
read_characters(args.scrivfile, scrivp)
read_places(args.scrivfile, scrivp)
read_bookinfo(args.scrivfile)

for item in manuscript.find('Children'):
    parse_binderitem(item)

plottr.write(plottrfile)

