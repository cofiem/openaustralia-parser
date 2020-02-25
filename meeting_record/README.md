# Meeting Records

This directory contains a set of Python 3.7 modules for extracting information from meeting records for various governments.

The model directory contains Python data classes that represent the parts of a document.

The raw directory contains the Python classes that extract the information from specific meeting record documents.


## Running tests

There are tests in the raw directory for each meeting record type.

Run them like this:

    $ cd meeting_record/raw
    $ python -m unittest


## Model Hierarchy

A file has two representations - the pages, each with a header and lines; and the document.

A document has sections, each with a header, paragraphs with lines, and possibly sub-sections.

In graph form: 

```
- File
--- List[Page]
    --- Header
        --- List[Line]
    --- List[Line]
--- Document
    --- List[Section]     <-|
        --- Header          |
            --- List[Line]  |
        --- List[Section] ->|
        --- List[Paragraph]
            --- List[Line]
```
