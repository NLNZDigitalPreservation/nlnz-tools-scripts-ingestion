# National Library of New Zealand Tools: Scripts for ingestion

Scripts related to Rosetta ingestion.

## Synopsis

This is a one-stop shop repository for scripts that are related to Rosetta ingestion. These
scripts do not fit into a traditional project paradigm (for example, they may be bash, python or groovy scripts that are run
independently of a project).

## Motivation

We want to keep track of our scripts to better share and support them.

## Important

Some of this scripting code code is related to the codebase *nlnz-tools-sip-generation-fairfax* found in the github
repository: https://github.com/NLNZDigitalPreservation/nlnz-tools-sip-generation-fairfax and there is an expectation
that the two codebases will work together.

## Versioning

These scripts are not under a project, so there are no versions associated with them, although each script may have a version
number embedded within.

## Installation

There are no artifacts that are created or installed.

## Scripts Reference

### fairfax-ingestion/fairfax-pre-and-post-process-grouper.py

Takes care of organising Fairfax files in two different stages:
1. When they are taken from a source location (such as a ftp folder) and organized for processing (this is a
   pre-processing target).
2. When they have been ingested into Rosetta and now need to be moved to a post-processed location for archiving.

This script has also been used to aggregate files and differentiate between those that have been processed and those
that have not been processed.

See the section *Folder structures* for descriptions of how folder structures are set up for pre-process and
post-process folders.

This script requires Python 2.7. It has not been tested with Python 3.

```
usage: fairfax-pre-and-post-process-grouper.py [-h]
       --source_folder SOURCE_FOLDER
       --target_pre_process_folder TARGET_PRE_PROCESS_FOLDER
       --target_post_process_folder TARGET_POST_PROCESS_FOLDER
       --for_review_folder FOR_REVIEW_FOLDER
       [--starting_date STARTING_DATE]
       [--ending_date ENDING_DATE]
       [--do_pre_processing]
       [--do_post_processing]
       [--do_list_unique_files]
       [--create_targets]
       [--pre_process_include_non_pdf_files]
       [--move_files] [--verbose]
       [--test]

Process pre-and-post processed Fairfax files by grouping them by date and
titleCode in appropriate pre-process and post-process folders.

optional arguments:
  -h, --help            show this help message and exit
  --source_folder SOURCE_FOLDER
                        The source-folder for the files for processing
  --target_pre_process_folder TARGET_PRE_PROCESS_FOLDER
                        The target folder for pre-processed files
  --target_post_process_folder TARGET_POST_PROCESS_FOLDER
                        The target folder for post-processed files
  --for_review_folder FOR_REVIEW_FOLDER
                        The target folder for unrecognized files
  --starting_date STARTING_DATE
                        The starting-date, format is yyyyMMdd
  --ending_date ENDING_DATE
                        The ending date, format is yyyyMMdd
  --do_pre_processing   Do pre-processing. The source folder is unprocessed files
                        (they will be checked against processed)
  --do_post_processing  Do post-processing. The source folder contains processed files with a'done' file for each group
  --do_list_unique_files List all files with unique filenames. The source folder is unprocessed files
  --create_targets      Indicates that the target folders will be created if they do not already exist
  --pre_process_include_non_pdf_files
                        Indicates that non-pdf files will be processed. By default only PDF files are processed.
  --move_files          Indicates that files will be moved to the target folder instead of copied
  --verbose             Indicates that operations will be done in a verbose manner
  --test                Indicates that only tests will be run
```

### fairfax-ingestion/fairfax-pre-process-grouper.sh

NOTE: This script is no longer being actively maintained. We recommend the use of the python script
fairfax-pre-and-post-process-grouper.py.

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

### fairfax-ingestion/recreate-fairfax-restore-structure.groovy

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

### fairfax-ingestion/recreate-files-with-structure.groovy

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

### reports/daily-file-usage-report.py

Provides a daily usage report of a set of subfolders of a given root folder.
```
usage: daily-file-usage-report.py [-h] --source_folder SOURCE_FOLDER
                                  --reports_folder REPORTS_FOLDER
                                  [--number_previous_days NUMBER_PREVIOUS_DAYS]
                                  [--create_reports_folder]
                                  [--include_file_details_in_console_output]
                                  [--calculate_md5_hash]
                                  [--include_dot_folders] [--verbose]
                                  [--debug] [--test]

daily-file-usage-report.py: Daily file usage report.

optional arguments:
  -h, --help            show this help message and exit
  --source_folder SOURCE_FOLDER
                        The root source-folder for the report.
  --reports_folder REPORTS_FOLDER
                        The folder where reports exist and get written.
  --number_previous_days NUMBER_PREVIOUS_DAYS
                        The number of previous days to include in the report.
                        The default is 0.
  --create_reports_folder
                        Indicates that the reports folder will get created. Otherwise it must already exist.
  --include_file_details_in_console_output
                        Indicates that individual file details will output to the console as well as the reports file.
  --calculate_md5_hash  Calculate and report the md5 hash of individual files (this is a very intensive I/O operation).
  --include_dot_directories
                        Include first-level root subdirectories that start with a '.'
  --verbose             Indicates that operations will be done in a verbose manner.
                        NOTE: This means that no csv report file will be generated.
  --debug               Indicates that operations will include debug output.
  --test                Indicates that only tests will be run.
```

Example usage:
```
sourceFolder=<location-of-ftp-subfolders-or...>
reportsFolder=<location-of-reports>

daily-file-usage-report.py \
    --source_folder "${sourceFolder}" \
    --reports_folder "${reportsFolder}" \
    --number_previous_days 7
```

## Folder structures

More descriptions on folder structures can be found in the github repository:
https://github.com/NLNZDigitalPreservation/nlnz-tools-sip-generation-fairfax

The expectation is that these different codebases work together with the same assumptions and structures.

### Pre-processing stage folder structure

Pre-processing takes place on a daily basis and files are processed by a given date and Title Code. The script
`fairfax-pre-and-post-process-grouper.py` will take a source group of files and put them in the following structure:
```
<targetPreProcessingFolder>/<date-in-yyyyMMdd-format>/<TitleCode>/{files for that titleCode and date}
```

### Ingested or post-processed stage folder structure

When files have been ingested into Rosetta, Rosetta places a `done` file at the root of the ingestion folder. Those
files are moved to the ingested or post-processed structure by a script, possibly
`fairfax-pre-and-post-process-grouper.py`. The folder structure for the ingested (post-processed) stage is as follows:
```
<targetPostProcessedFolder>/<magazines|newspapers>/<TitleCode>/<yyyy>/<date-in-yyyyMMdd-format>
```
In this dated folder, the file structure matches the same structure that was ingested into Rosetta, namely:
```
<date-in-yyyyMMdd-format>
   |- done
   |- content/
           |- mets.xml
           |- streams/
                   |- <pdf-files>
```
Note that the `mets.xml` file is placed in the `content` folder. The `done` files is in the root `yyyyMMdd` folder.

## Tests

The scripts contain no validation tests except as noted within the script itself.

## Contributors

See git commits to see who contributors are. Issues are tracked through the git repository issue tracker.

## License

&copy; 2019 National Library of New Zealand. All rights reserved. MIT license.
