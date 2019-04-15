# National Library of New Zealand Tools: Scripts for ingestion

Scripts related to Rosetta ingestion.

## Synopsis

This is a one-stop shop repository for scripts that are related to Rosetta ingestion. These
scripts do not fit into a traditional project paradigm (for example, they may be bash, python or groovy scripts that are run
independently of a project).

## Motivation

We want to keep track of our scripts to better share and support them.

## Important

At this time there is no important information to impart.

## Versioning

These scripts are not under a project, so there are no versions associated with them, although each script may have a version
number embedded within.

## Installation

There are no artifacts that are created or installed.

## Scripts Reference

### fairfax-pre-process-grouper.sh

Takes Fairfax files that are in a set of directories or subdirectories and reorganizes them with the following structure:
```
<targetFolder>
    |- <date-1>
    |    |- <titleCode>
    |        |- <files>
    |- <date-2>

<forReviewFolder>
    |- <UNPROCESSED>
         |- <files>
```

Example usage:
```
scriptLocation="/path/to/the/script/location"

sourceFolder="/path/to/unprocessed-fairfax-files"
targetFolder="/path/to/pre-processed-fairfax-files"
forReviewFolder="/path/to/for-review-files"
startingDate="20171001"
endingDate="20191231"
createDestination=true
moveFiles=false

${scriptLocation}/fairfax-pre-process-grouper.sh \
    --startingDate="${startingDate}" \
    --endingDate="${endingDate}" \
    --createDestination="${createDestination}" \
    --moveFiles="${moveFiles}" \
    --sourceFolder="${sourceFolder}" \
    --targetFolder="${targetFolder}" \
    --forReviewFolder="${forReviewFolder}"
```

### recreate-fairfax-restore-structure.groovy

Recreates the `Fairfax-RESTORE` structure in another directory using sample files. This is to allow testing of the processing of
Fairfax files without using actual Fairfax files. The `sourceFileListingPath` is a text file containing a listing of all the
files that are recreated in a different directory structure. There is an expectation that `sourceFileListingPath` has
`/Fairfax-RESTORE/` in the path. This is the cutoff point in the file path -- the file path after this point is recreated in the
`destinationFolder`. The sample PDF file is simply copied over for every entry. For ease and speed of processing it's recommended
that the sample files be as small as possible.

Example usage:
```
scriptLocation="/path/to/the/script/location"

sourceFileListingPath="/path/to/source-files"
destinationFolder="/path/to/destination"
samplePdfFilePath="/path/to/sample-pdf-file"

${scriptLocation}/recreate-fairfax-restore-structure.groovy \
    "${sourceFileListingPath}" \
    "${destinationFolder}" \
    "${samplePdfFilePath}"
```

### recreate-files-with-structure.groovy

Recreates files with a directory structure in another directory using sample files. This is to allow testing of the processing
of that particular structure without using actual Fairfax files (or some other set of files that we don't want to move out of a
secure space). The `sourceFileListingPath` is a text file containing a listing of all the files that are recreated in a different
file root, but having the same directory structure. The `sourceFileListingPath` is the cutoff point in the file path. The file path
after this point is recreated in the `targetFolder`. The sample PDF file, sample `mets.xml`, sample `done` and sample other file
are simply copied over for every matching entry. For ease and speed of processing it's recommended that the sample files be as
small as possible.

Example usage:
```
scriptLocation="/path/to/the/script/location"

sourceFileListingPath="/path/to/source-files"
targetFolder="/path/to/destination"
# the file structure after the cutoff is recreated in the destination folder
sourceFileFilenameCutoff="/LD/Fairfax/"
# PDF files have a filename suffix of '.pdf'
samplePdfFilePath="/path/to/sample-pdf-file"
# The mets file has a filename of 'mets.xml'
sampleMetsFilePath="/path/to/sample/mets.xml"
# The done file has a filename of 'done'
sampleDoneFilePath="/path/to/sample/done"
sampleOtherFilePath="/path/to/any-other-file-substitute"

${scriptLocation}/recreate-files-with-structure.groovy \
    "${sourceFileListingPath}" \
    "${targetFolder}" \
    "${sourceFileFilenameCutoff}" \
    "${samplePdfFilePath}" \
    "${sampleMetsFilePath}" \
    "${sampleDoneFilePath}" \
    "${sampleOtherFilePath}"
```

## Tests

The scripts contain no validation tests except as noted within the script itself.

## Contributors

See git commits to see who contributors are. Issues are tracked through the git repository issue tracker.

## License

&copy; 2019 National Library of New Zealand. All rights reserved. MIT license.
