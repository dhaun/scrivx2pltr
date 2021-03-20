# About this script

## A few words on what's happening behind the scenes in this script (without going into too much detail).

The, let's call them "data models", of Scrivener and Plottr have some obvious similarities but also some differences, some huge, some more subtle. For example, it's obvious that you can map a file in Scrivener's binder to a scene card in Plottr.

Characters, to pick another example, are not so easy. In Plottr, each character has a dedicated card, with special attributes and fields that you can fill in. You can also define which characters are in which scene. In Scrivener, characters are much more free-form. In fact, there's only a "Characters" folder in the default project template but what you do with it (or whether you use it at all) is up to you. And even If you use it, you'd typically just have a document named after your character in that folder and all the character's attributes are kept inside that document, making it pretty much impossible to transfer over to Plottr in a structured way. Characters are also not easily associated with scenes, so people use Scrivener labels or keywords as workarounds.

This is why there are various options that you may need to use in order to get your Scrivener meta data over into the Plottr file properly - heavily depending on what you're using and how. Some use cases may not be covered yet. In that case, feel free to open an issue or, better yet, send a pull request with a fix :)

The options `--maxCharacters` and `--maxPlaces` exist since while I tend to have one file for each character and each place, I also keep files with lists of minor characters or additional information about groups of characters in the characters folder. Since those aren't characters by Plottr's definition, I want to skip them when exporting to Plottr, limiting the export to the first *n* character files.

## Associating characters with scenes

Scrivener keywords are one way to associate scenes with characters. In one of my projects, I have a keyword for each main character and then assigned the keywords for all the characters in a specific scene to the respective file. To transfer that information over to Plottr, I use the `--keywordsAreCharacters` option. It assumes that for each keyword there is a character file with the same name.

Similarly, you can use Scrivener labels to make the association with a scene. I use a label for each character from whom's perspective a scene is written and label the scene files accordingly. This information can be transferred over to Plottr with the `--labelsAreCharacters` option.

Note: You can use both `--labelsAreCharacters` and `--keywordsAreCharacters`. In that case, labels are handled first, meaning that the labelled character will appear first in the list. Duplicates are of course detected.

There are no corresponding options for places, mainly because I haven't had the need for it. They should be easy to implement, though. Let me know.

Scenes can be coloured in Scrivener, using a label's colour. To transfer label colours over to Plottr, use `--useLabelColors` (apologies for the mix of BE and AE here - the code uses AE spelling, but I write mostly in BE).

Yet another approach is to use Scrivener keywords as tags in Plottr. With the option `--keywordsAreTags`, the script will do exactly that. You can also combine this with `--labelsAreCharacters` and/or `--keywordsAreCharacters`. While this would create some redundant information, it may help getting a quick overview since Plottr shows tags in a popup when you hover over a scene card whereas to see the characters in a scene, you have to edit the card.

## What else?

Scrivener synopsis (the text you can write into a card in Scrivener) is carried over for scenes, characters, and places. I do not plan to copy over the actual text of a scene, since that would not make sense. You're supposed to only plot in Plottr, but write the scene out in Scrivener.

For characters and places, as well as general notes (for which Plottr has a separate section), I'm still looking for the best way to handle the RTF that Scrivener uses internally. So far, I only found working Python code that strips all formatting. It would be better than nothing, though, I guess.

Images you put into the inspector for characters and places are carried over. I could do the same for scenes, but Plottr doesn't have a place for images in scene cards (yet?).

## Unused Plottr features

There are also things in Plottr that have no obvious equivalent in Scrivener.

Characters in Plottr have a category, so that you can label them a main or supporting character. As of now, all characters are labelled as main characters when exporting from Scrivener. I wouldn't know how to mark a character as "supporting" in Scrivener that easily carries over to Plottr.

There's also no standard way to handle book series in Scrivener. You would normally have just one book of a series active, ie. in your drafts folder, ready to be compiled. Additional books would either have their own projects or you would keep them in separate (and thus non-standard) folders.

## What's next?

At this point, the script does most of what I need it to do, with the exception of the character and places descriptions (and possibly notes). For those, I'm waiting for inspiration on how to handle the RTF.

Other than that, I'm open to ideas (and pull requests).
