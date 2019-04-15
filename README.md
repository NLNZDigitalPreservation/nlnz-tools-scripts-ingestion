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

logit ${scriptLocation}/fairfax-pre-process-grouper.sh \
    --startingDate="${startingDate}" \
    --endingDate="${endingDate}" \
    --createDestination="${createDestination}" \
    --moveFiles="${moveFiles}" \
    --sourceFolder="${sourceFolder}" \
    --targetFolder="${targetFolder}" \
    --forReviewFolder="${forReviewFolder}"
```

## Tests

The scripts contain no validation tests except as noted within the script itself.

## Contributors

See git commits to see who contributors are. Issues are tracked through the git repository issue tracker.

## License

&copy; 2019 National Library of New Zealand. All rights reserved. MIT license.
