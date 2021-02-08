This directory contains the UAS Documentation in `uas_overview.md` and associated graphics, and a table of contents generator for that documentation in `mktoc.sh`.  When updating the document, if you add a new section or delete a section, please make sure you follow the convention in the document for placing an HTML anchor on the new section's section heading line and then re-generate the table of contents.  This is done by running:

```
./mktoc.sh uas_overview.md > toc
```

and then editing `uas_overview.md` to replace the existing table of contents in section 1 of the document.

