========
ZERRPHIX
========

Overview
--------

Zerrphix is a new HDI DUNE index and skinner written in python.

The major difference between Zerrphix and other HDI Dune indexers and skinners is that Zerrphix uses
the dune_http functionality. This essentially means that the UI structure is obtained from a web server
rather than a folder structure using dune_folder.txt (e.g. Yadis).

It should be noted that there is a big caveat to using Zerrphix which is that a Linux computer needs
to be running Zerrphix (pretty much 24/7) for the dune to be able to use the Zerrphix UI at any time.
The raspberry pi has been tested and looks to be suitable.

Current Features
----------------

- Real-time dynamic menu structure generation
- Designed to be fully automated such that once a new film/show is detected and processed,
  from a pre configured scan path, it is available on the Zerrphix UI.
- Highly customisable menu structure/templates
- Multi user support
- Template per user support
- Film TV/Search on the dune
- Shows last film/show watched on user's main menu
- Continue and Watch Next functionality for TV Show Episodes
- Add Favourites/To Watch for Film and TV from the dune
- Each user can have their own language set (images and text)
- Each user can have a customised title, overview for film/show/show episode
- Multi Dune support

Roadmap
-------

- Allow custom plugins to allow for other online databases lookups (tmdb/thetvdb already supported)

Installation
------------

https://docs.google.com/document/d/1SXcNiFSxuZPI2cABDHOrdCOsF-_8BEgjLonA2R31ZOM/edit?usp=sharing


Usage
-----

https://docs.google.com/document/d/1B-R4R3x74G0xGZjDC0SjLlXQ0rggPLNrX7Hgy86Htjk/edit?usp=sharing

IRC
---

https://webchat.freenode.net/?channels=zerrphix