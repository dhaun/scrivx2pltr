# scrivx2pltr

## What it does

Creates a Plottr file from a Scrivener project.
All the scenes in the Scrivener project's Manuscript folder will show up as Scene Cards in Plottr, with their respective title and synopsis.


## What it doesn't do

It does not and never will synchronise between Plottr and Scrivener. 
Plottr can already export to Scrivener and they are supposedly [working on synchronisation](https://plottr.com/our-roadmap/), too.


## What it sort-of does

Characters and Places are created from files in the respective Scrivener folders. Images are exported, too. The content of the files is still missing, though, mostly due to lack of an idea how to parse RTF into something Plottr can understand. 


## What it doesn't do yet

Export notes and labels.
There are no standards for those in Scrivener, though.


## Requirements

- Python 3
- [Scrivener 3](https://www.literatureandlatte.com/scrivener/overview)
- a current version of [Plottr](https://plottr.com/) (they made some changes to the file format in early 2021)


## Caveats and Side Effects

- Haven't tested this on Windows.
- The file formats of both Scrivener and Plottr are undocumented. They may change at any time, breaking this script.
- Use at your own risk and always make backups first.


## Who wrote this?

My name is Dirk Haun. I used to be a software engineer but have been doing other things for the past 5+ years. I also haven't written any Python in as many years, so please bear with me.


## Which license is this under?

MIT License, for now. I may change my mind at a later point, but for now there isn't a lot here that's worth protecting anyway. It'll always be open source under an OSI-approved license, promised!
