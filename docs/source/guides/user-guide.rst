==========
User Guide
==========

Introduction
============

About NLNZ Tools Scripts Ingestion
----------------------------------

NLNZ Tools Scripts Ingestion is a set of scripts related to the processing of SIPs for ingestion into the Rosetta
archiving system. The aim is to useful tools to help in that processing.

Contents of this document
-------------------------

Following this introduction, this User Guide includes the following sections:

-   **Fairfax ingestion related scripts**  - Covers Fairfax ingestion related scripts.

-   **Reports scripts** - Covers reports-related scripts.

-   **Utilities scripts** - Covers useful utility scripts.

-   **Running requirements** - Covers running requirements.


Fairfax ingestion related scripts
=================================

fairfax-ingestion/fairfax-pre-and-post-process-grouper.py
-------------------------------------------------------------
Process pre-and-post processed Fairfax files by grouping them by date and titleCode in appropriate pre-process and
post-process folders.

WARNING
~~~~~~~
This script is not in active use, but is kept for reference.

Uses
~~~~

Takes care of organising Fairfax files in two different stages:

    1. When they are taken from a source location (such as a ftp folder) and organized for processing (this is a
       pre-processing target).
    2. When they have been ingested into Rosetta and now need to be moved to a post-processed location for archiving.

This script has also been used to aggregate files and differentiate between those that have been processed and those
that have not been processed.

Note that this script does not conform to the folder structures used by nlnz-tools-sip-generation-fairfax. See the
documentation https://nlnz-tools-sip-generation-fairfax.readthedocs.io for more details.

Requirements
~~~~~~~~~~~~
This script requires Python 2.7. It has not been tested with Python 3.

Arguments
~~~~~~~~~
Arguments are as follows::

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

Command line usage
~~~~~~~~~~~~~~~~~~
The command line usage is as follows::

    fairfax-pre-and-post-process-grouper.py [-h]
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

fairfax-ingestion/fairfax-pre-process-grouper.sh
----------------------------------------------------
Takes Fairfax files that are in a set of directories or subdirectories and reorganizes them into a given structure.

WARNING
~~~~~~~
NOTE: This script is no longer being actively maintained. We recommend the use of the python script
```fairfax-pre-and-post-process-grouper.py```.

Target structure
~~~~~~~~~~~~~~~~
The target folder/file structure::

    <targetFolder>
        |- <date-1>
        |    |- <titleCode>
        |        |- <files>
        |- <date-2>

    <forReviewFolder>
        |- <UNPROCESSED>
             |- <files>

Example usage
~~~~~~~~~~~~~
An example of using this script::

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

fairfax-ingestion/recreate-fairfax-restore-structure.groovy
---------------------------------------------------------------
Recreates the ``Fairfax-RESTORE`` structure in another directory using sample files. This is to allow testing of the
processing of Fairfax files without using actual Fairfax files. The ``sourceFileListingPath`` is a text file containing
a listing of all the files that we want to recreate. This listing would likely be created by doing something like
``find . -type f | sort > list-files.txt``.

The files in the listing file are then recreated in a different directory structure. There is an expectation that
``sourceFileListingPath`` has ``/Fairfax-RESTORE/`` in the path. This is the cutoff point in the file path -- the file
path after this point is recreated in the ``destinationFolder``. The sample PDF file is simply copied over for every
entry. For ease and speed of processing we recommend that the sample files be as small as possible.

Example usage
~~~~~~~~~~~~~
The following example shows how to use the script::

    scriptLocation="/path/to/the/script/location"

    sourceFileListingPath="/path/to/source-files"
    destinationFolder="/path/to/destination"
    samplePdfFilePath="/path/to/sample-pdf-file"

    ${scriptLocation}/recreate-fairfax-restore-structure.groovy \
        "${sourceFileListingPath}" \
        "${destinationFolder}" \
        "${samplePdfFilePath}"

fairfax-ingestion/recreate-files-with-structure.groovy
----------------------------------------------------------
Recreates files with a directory structure in another directory using sample files. (This is a more generic version of
``recreate-fairfax-restore-structure.groovy``). This scripts allows testing of the processing of that particular
structure without using actual Fairfax files (or some other set of files that we don't want to move out of a
secure space).

Parameters
~~~~~~~~~~
``sourceFileListingPath``
    A text file containing a listing of all the files that are recreated in a different file root, but having the same
    directory structure. This listing would likely be created by doing something like
    ``find . -type f | sort > list-files.txt``.

``sourceFileListingPath``
    This is the cutoff point in the file path. The file path after this point is recreated in the ``targetFolder``.
    The sample PDF file, sample `mets.xml`, sample `done` and sample other file are simply copied over for every
    matching entry. For ease and speed of processing it's recommended that the sample files be as small as possible.

Resource files
~~~~~~~~~~~~~~
Sample resource files are found in the ``fairfax-ingestion/resources`` folder.

Example usage
~~~~~~~~~~~~~
::

    scriptLocation="/path/to/the/script/location"

    sourceFileListingPath="/path/to/source-files"
    targetFolder="/path/to/destination"
    # the file structure after the cutoff is recreated in the destination folder
    sourceFileFilenameCutoff="/LD/Fairfax/"
    # PDF files have a filename suffix of '\.[pP]{1}[dD]{1}[fF]{1}'
    samplePdfFilePath="resources/sample.pdf"
    # The mets file has a filename of 'mets.xml'
    sampleMetsFilePath="resources/mets.xml"
    # The done file has a filename of 'done'
    sampleDoneFilePath="resources/done"
    sampleOtherFilePath="resources/other-file.txt"

    ${scriptLocation}/recreate-files-with-structure.groovy \
        "${sourceFileListingPath}" \
        "${targetFolder}" \
        "${sourceFileFilenameCutoff}" \
        "${samplePdfFilePath}" \
        "${sampleMetsFilePath}" \
        "${sampleDoneFilePath}" \
        "${sampleOtherFilePath}"

Reports scripts
===============

reports/daily-file-usage-report.py
----------------------------------
Provides a daily usage report of a set of subfolders of a given root folder.

Arguments
~~~~~~~~~
::

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
    --ignore_unchanged_directories
                        Do not report changes for directories that haven't changed.
    --verbose             Indicates that operations will be done in a verbose manner.
                        NOTE: This means that no csv report file will be generated.
    --debug               Indicates that operations will include debug output.
    --test                Indicates that only tests will be run.

Usage
~~~~~
::

    daily-file-usage-report.py [-h] --source_folder SOURCE_FOLDER
                                      --reports_folder REPORTS_FOLDER
                                      [--number_previous_days NUMBER_PREVIOUS_DAYS]
                                      [--create_reports_folder]
                                      [--include_file_details_in_console_output]
                                      [--calculate_md5_hash]
                                      [--include_dot_folders] [--verbose]
                                      [--debug] [--test]

Example usage
~~~~~~~~~~~~~
::

    scriptsFolder="/go/repos-nlnzdigitalpreservation/nlnz-tools-scripts-ingestion/reports"
    sourceFolder="/media/legaldep-ftp"
    reportsFolder="/media/sf_a-laptop-shared-work/ftp-daily-usage-reports"

    ${scriptsFolder}/daily-file-usage-report.py \
        --source_folder "${sourceFolder}" \
        --reports_folder "${reportsFolder}" \
        --ignore_unchanged_directories \
        --number_previous_days 21


Report output
~~~~~~~~~~~~~
The console output to the report can be used in a csv file. There is also a csv file generated in the ``reports_folder``
that contains a detailed listing ``.csv`` of the source folders. This report csv file is then used as input for the
next report, as long as it was generated within the ``number_previous_days``.


Utilities scripts
=================

utilities/bulk-file-rename.py
-----------------------------
Simple utility for renaming files in bulk.

Arguments
~~~~~~~~~
::

    -h, --help            show this help message and exit
    --source_folder SOURCE_FOLDER
                        The root source-folder for the report.
    --file_name_portion_to_replace FILE_NAME_PORTION_TO_REPLACE
                        The portion of the filename that will be replacement.
    --file_name_portion_replacement FILE_NAME_PORTION_REPLACEMENT
                        The replacement portion of the filename. If not specified, then an empty string is used.
    --verbose             Indicates that operations will be done in a verbose
                        manner. NOTE: This means that no csv report file will
                        be generated.
    --debug               Indicates that operations will include debug output.
    --test                Indicates that only tests will be run.

Usage
~~~~~
::

    usage: bulk-file-rename.py [-h] --source_folder SOURCE_FOLDER \
                               --file_name_portion_to_replace FILE_NAME_PORTION_TO_REPLACE \
                               --file_name_portion_replacement FILE_NAME_PORTION_REPLACEMENT \
                               [--verbose] [--debug] \
                               [--test]

Running requirements
====================

Python-based scripts
--------------------
Those scripts with a ``.py`` extension are Python-based scripts. Currently these scripts run with Python 2.7. None
of the scripts have been upgraded to Python3.

Groovy-based scripts
--------------------
Those scripts with a ``.groovy`` extension are Groovy-based. Currently these scripts run with Groovy 2.5.4 or later and
Java OpenJDK 11.

Operating system
----------------
These scripts have only been tested and run on Ubuntu Linux 18.
