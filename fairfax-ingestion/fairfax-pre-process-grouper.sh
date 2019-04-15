#!/bin/bash

# fairfax-pre-process-grouper.sh
# Group source files by date and titleCode.
# Output is used by readyForIngestion.
# Requires sourceFolder, targetFolder, forReviewFolder.
# Uses startingDate, endingDate.
# Optional createDestination, moveFiles.

# Using gist https://gist.github.com/jehiah/855086 for parsing shell script arguments

createDestination="true"
moveFiles="false"
verbose="false"
startingDate=20140101
endingDate=20190630
moveOrCopyFlags=""

function show_usage() {
    echo "Pre-processes Fairfax files by grouping them by date and titleCode."
    echo ""
    echo "$0"
    echo -e "\t-h --help"
    echo -e "\t--sourceFolder=<source-folder>"
    echo -e "\t--targetFolder=<target-folder>"
    echo -e "\t--forReviewFolder=<for-review-folder>"
    echo -e "\t--startingDate=<starting-date>, format is yyyyMMdd, default is ${startingDate}"
    echo -e "\t--endingDate=<ending-date>, format is yyyyMMdd, default is ${endingDate}"
    echo -e "\t--createDestination=<create-destination-folders>, default is ${createDestination} (otherwise use false)"
    echo -e "\t--moveFiles=<move-files-to-destination>, default is ${moveFiles} (otherwise use true)"
    echo ""
}

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        --sourceFolder)
            sourceFolder=$VALUE
            ;;
        --targetFolder)
            targetFolder=$VALUE
            ;;
        --forReviewFolder)
            forReviewFolder=$VALUE
            ;;
        --startingDate)
            startingDate=$VALUE
            ;;
        --endingDate)
            endingDate=$VALUE
            ;;
        --createDestination)
            createDestination=$VALUE
            ;;
        --moveFiles)
            moveFiles=$VALUE
            ;;
        --verbose)
            verbose=$VALUE
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

UNACCEPTABLE_PARAMETERS=false

# Check variables
if [ -n "$startingDate" ]; then
    echo "startingDate=${startingDate}"
    if date -d "$startingDate"; then
        startingYear=`date -d "${startingDate}" +"%Y"`
        startingMonth=`date -d "${startingDate}" +"%m"`
        startingDay=`date -d "${startingDate}" +"%d"`
        echo -e "\tstartingYear=${startingYear}, startingMonth=${startingMonth}, startingDay=${startingDay}"
     else
        UNACCEPTABLE_PARAMETERS=true
    fi
else
    echo "ERROR startingDate has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [ -n "$endingDate" ]; then
    echo "endingDate=${endingDate}"
    if date -d "$endingDate"; then
        endingYear=`date -d "${endingDate}" +"%Y"`
        endingMonth=`date -d "${endingDate}" +"%m"`
        endingDay=`date -d "${endingDate}" +"%d"`
        echo -e "\tendingYear=${endingYear}, endingMonth=${endingMonth}, endingDay=${endingDay}"
     else
        UNACCEPTABLE_PARAMETERS=true
    fi
else
    echo "ERROR endingDate has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

if (( ${startingDate} > ${endingDate} )); then
    echo ""
    echo "ERROR startingDate=${startingDate} must be BEFORE endingDate=${endingDate}"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [ -n "$createDestination" ]; then
    echo "createDestination=${createDestination}"
else
    echo "ERROR createDestination has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [ -n "$verbose" ]; then
    echo "verbose=${verbose}"
    if [[ "$verbose" == "$true" ]]; then
        moveOrCopyFlags="-v"
    else
        moveOrCopyFlags=""
    fi
else
    echo "ERROR verbose has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [ -n "$moveFiles" ]; then
    echo "moveFiles=${moveFiles}"
else
    echo "ERROR moveFiles has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [ -n "$sourceFolder" ]; then
    echo "sourceFolder=${sourceFolder}"
    if [ -d "${sourceFolder}" ]; then
        echo -e "\tsourceFolder=${sourceFolder} exists, processing can take place."
    else
        echo -e "\tERROR sourceFolder=${sourceFolder} must exist!"
        UNACCEPTABLE_PARAMETERS=true
    fi
else
    echo "ERROR sourceFolder has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [ -n "$targetFolder" ]; then
    echo "targetFolder=${targetFolder}"
    if [ -d "${targetFolder}" ]; then
        echo -e "\ttargetFolder=${targetFolder} exists."
    else
        if [[ "$createDestination" == "true" ]]; then
            mkdir -pv "${targetFolder}"
        else
            echo -e "\tERROR $createDestination=${createDestination}, therefore targetFolder=${targetFolder} must exist!"
            UNACCEPTABLE_PARAMETERS=true
        fi
    fi
else
    echo "ERROR targetFolder has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [ -n "$forReviewFolder" ]; then
    echo "forReviewFolder=${forReviewFolder}"
    if [ -d "${forReviewFolder}" ]; then
        echo -e "\tforReviewFolder=${forReviewFolder} exists."
    else
        if [[ "$createDestination" == "true" ]]; then
            mkdir -pv "${forReviewFolder}"
        else
            echo -e "\tERROR $createDestination=${createDestination}, therefore forReviewFolder=${forReviewFolder} must exist!"
            UNACCEPTABLE_PARAMETERS=true
        fi
    fi
else
    echo "ERROR forReviewFolder has not been set!"
    UNACCEPTABLE_PARAMETERS=true
fi

echo ""

if [[ "$UNACCEPTABLE_PARAMETERS" == "true" ]]; then
    echo ""
    echo "Parameters are incomplete or incorrect. Please try again."
    echo ""
    echo "Usage:"
    show_usage
    exit 1
fi

echo ""
echo ""
currentTime=`date +"%Y-%m-%d %H:%M:%S"`
echo "${currentTime}: STARTED"

function processFile() {
    fileToProcess=$1
    echo "PROCESSING fileToProcess=${fileToProcess}, targetFolder=${targetFolder}"
}

completeFilesList=()

function get_all_pdf_files() {
    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${currentTime}: Starting to find all pdf/PDF files for sourceFolder=${sourceFolder}"

    #find ${sourceFolder} -iname "*.pdf"

    while IFS=  read -r -d $'\0'; do
        completeFilesList+=("$REPLY")
    done < <(find ${sourceFolder} -iname "*.pdf" -print0)

    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${currentTime}: Found ${#completeFilesList[@]} matching files."
}

function sort_complete_files_list() {
    IFS=$'\n' sortedCompleteFilesList=($(sort <<<"${completeFilesList[*]}"))
    unset IFS
}

isSameFile="false"

function are_files_the_same() {
    firstFilePath="$1"
    secondFilePath="$2"

    md5FirstFilePathArray=($(md5sum "${firstFilePath}"))
    md5FirstFilePath=${md5FirstFilePathArray[0]}

    md5SecondFilePathArray=($(md5sum "${secondFilePath}"))
    md5SecondFilePath=${md5SecondFilePathArray[0]}

    if [[ "${verbose}" == "true" ]]; then
        echo "$firstFilePath} md5=${md5FirstFilePath}, ${secondFilePath} md5=${md5SecondFilePath}"
    fi

    if [[ "${md5FirstFilePath}" == "${md5SecondFilePath}" ]]; then
        isSameFile="true"
        if [[ "${verbose}" == "true" ]]; then
            echo "${firstFilePath} md5=${md5FirstFilePath} is the same as ${secondFilePath} md5=${md5SecondFilePath}"
        fi
    else
        isSameFile="false"
        echo "${firstFilePath} md5=${md5FirstFilePath} is NOT the same as ${secondFilePath} md5=${md5SecondFilePath}"
    fi
}

nonDuplicateFilename=

function non_duplicate_filename() {
    testFilename="$1"
    # assume shopt -s nocasematch has already been set
    #echo "non_duplicate_filename CALLED with testFilename=${testFilename}"
    nonDuplicateRegex="(.*)\\/(.*)(\\.pdf)"
    if [[ $testFilename =~ ${nonDuplicateRegex} ]]; then
        count=0
        testPathOnly="${BASH_REMATCH[1]}"
        testFilenameRoot="${BASH_REMATCH[2]}"
        testFilenameExtension="${BASH_REMATCH[3]}"
        nonDuplicateFilename="${testFilenameRoot}${testFilenameExtension}"
        #echo "nonDuplicateFilename=${nonDuplicateFilename}"
        testFullFile="${testPathOnly}/${nonDuplicateFilename}"
        while [ -f "${testFullFile}" ]; do
            nonDuplicateFilename="${testFilenameRoot}-DUPLICATE-${count}${testFilenameExtension}"
            testFullFile="${testPathOnly}/${nonDuplicateFilename}"
            count=$((count + 1))
        done
    fi

    #echo "nonDuplicateFilename=${nonDuplicateFilename}"
}

function process_for_date() {
    processingDate=$1
    currentYear=`date -d "${processingDate}" +"%Y"`
    currentMonth=`date -d "${processingDate}" +"%m"`
    currentDay=`date -d "${processingDate}" +"%d"`

    currentProcessingSet=("${unprocessedSortedCompleteFilesList[@]}")
    unprocessedSortedCompleteFilesList=()

    regexForDate="(.*?)\\/(\\w{5,7})(-${processingDate}-\\w{3,4}.*?\\.pdf)"
    echo ""
    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo -e "${currentTime}: Processing ${currentYear}-${currentMonth}-${currentDay} with regex=${regexForDate}"

    # set nocasematch option
    shopt -s nocasematch

    echo "regexForDate=${regexForDate}"
    for currentFilePath in "${currentProcessingSet[@]}"; do
        if [[ ${currentFilePath} =~ ${regexForDate} ]]; then
            #echo "Match ${processingDate} with ${currentFilePath}, full match=${BASH_REMATCH[0]}"
            currentFilePathOnly="${BASH_REMATCH[1]}"
            titleCode="${BASH_REMATCH[2]}"
            targetFolderForFile="${targetFolder}/${processingDate}/${titleCode}"
            restOfFilename="${BASH_REMATCH[3]}"
            # echo "currentFilePathOnly=${currentFilePathOnly}, titleCode=${titleCode}, restOfFilename=${restOfFilename}"
            currentSourceFilename="${titleCode}${restOfFilename}"
            targetFilename="${currentSourceFilename}"
            mkdir -pv "${targetFolderForFile}"
            if [ -f "${targetFolderForFile}/${targetFilename}" ]; then
                non_duplicate_filename "${targetFolderForFile}/${targetFilename}"
                targetFilename="${nonDuplicateFilename}"
                echo "WARNING Duplicate ${currentSourceFilename} renamed to ${targetFilename}"
            fi
            if [[ "${moveFiles}" == "true" ]]; then
                mv -n ${moveOrCopyFlags} "${currentFilePath}" "${targetFolderForFile}/${targetFilename}"
            else
                cp -a ${moveOrCopyFlags} "${currentFilePath}" "${targetFolderForFile}/${targetFilename}"
            fi
        else
            unprocessedSortedCompleteFilesList+=("${currentFilePath}")
            #echo "NO Match ${processingDate} with ${currentFilePath}"
        fi
    done

    # TODO We could remove files from the completeFilesList that we haven't processed
    # unset nocasematch option
    shopt -u nocasematch
}

function process_via_start_date_to_end_date() {
    echo ""
    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${currentTime}: START Processing using process_via_start_date_to_end_date"

    unprocessedSortedCompleteFilesList=("${sortedCompleteFilesList[@]}")

    currentDate=${startingDate}
    while (( ${currentDate} <= ${endingDate} )); do
            process_for_date $currentDate

            currentDate=`date -d "${currentDate}+1day" +"%Y%m%d"`
    done

    echo ""
    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${currentTime}: Processing unmatched files"

    targetFolderForUnprocessed="${forReviewFolder}/UNPROCESSED"
    mkdir -pv "${targetFolderForUnprocessed}"

    for currentFilePath in "${unprocessedSortedCompleteFilesList[@]}"; do
        echo "Unprocessed=${currentFilePath}"
        if [[ "${moveFiles}" == "true" ]]; then
            mv -n ${moveOrCopyFlags} "${currentFilePath}" "${targetFolderForUnprocessed}"
        else
            cp -a ${moveOrCopyFlags} "${currentFilePath}" "${targetFolderForUnprocessed}"
        fi
    done

    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${currentTime}: END Processing using process_via_start_date_to_end_date"
    echo ""
}

function process_for_given_file() {
    currentFilePath=$1
    unprocessedFolder=$2

    currentProcessingSet=("${unprocessedSortedCompleteFilesList[@]}")
    unprocessedSortedCompleteFilesList=()

    # NOTE some of these regexes match differently based on the version of unix operating
    regexForFile="(.*?)\\/(\\w{5,7})-([0-9]{8})(-\\w{3,4}.*?\\.pdf)"

    if [[ "${verbose}" == "true" ]]; then
        currentTime=`date +"%Y-%m-%d %H:%M:%S"`
        echo -e "${currentTime}: Processing currentFilePath=${currentFilePath} with regex=${regexForFile}"
    fi

    if [[ ${currentFilePath} =~ ${regexForFile} ]]; then
        #echo "Match ${regexForFile} with ${currentFilePath}, full match=${BASH_REMATCH[0]}"
        currentFilePathOnly="${BASH_REMATCH[1]}"
        titleCode="${BASH_REMATCH[2]}"
        fileDate="${BASH_REMATCH[3]}"
        restOfFilename="${BASH_REMATCH[4]}"
        targetFolderForFile="${targetFolder}/${fileDate}/${titleCode}"
        # echo "currentFilePathOnly=${currentFilePathOnly}, titleCode=${titleCode}, restOfFilename=${restOfFilename}"
        currentSourceFilename="${titleCode}-${fileDate}${restOfFilename}"
        targetFilename="${currentSourceFilename}"
        processFile="true"
        if (( ${fileDate} > ${startingDate} && ${fileDate} <= ${endingDate} )); then
            mkdir -pv "${targetFolderForFile}"
            if [ -f "${targetFolderForFile}/${targetFilename}" ]; then
                are_files_the_same "${currentFilePath}" "${targetFolderForFile}/${targetFilename}"
                if [[ "${isSameFile}" == "true" ]]; then
                    processFile="false"
                    printf "-"
                else
                    processFile="true"
                    non_duplicate_filename "${targetFolderForFile}/${targetFilename}"
                    targetFilename="${nonDuplicateFilename}"
                    echo "WARNING Duplicate ${currentSourceFilename} renamed to ${targetFilename}"
                fi
            fi
            if [[ "${processFile}" == "true" ]]; then
                printf "."
                if [[ "${currentSourceFilename}" == "${targetFilename}" ]]; then
                    actualTarget="${targetFolderForFile}"
                else
                    actualTarget="${targetFolderForFile}/${targetFilename}"
                fi
                #echo "actualTarget=${actualTarget}"
                if [[ "${moveFiles}" == "true" ]]; then
                    mv -n ${moveOrCopyFlags} "${currentFilePath}" "${actualTarget}"
                else
                    cp -a ${moveOrCopyFlags} "${currentFilePath}" "${actualTarget}"
                fi
            fi
        fi
    else
        # TODO Need to dedupe
        if [[ "${moveFiles}" == "true" ]]; then
            mv -n ${moveOrCopyFlags} "${currentFilePath}" "${unprocessedFolder}"
        else
            cp -a ${moveOrCopyFlags} "${currentFilePath}" "${unprocessedFolder}"
        fi
    fi
}

function process_via_going_through_all_files() {
    echo ""
    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${currentTime}: START Processing using process_via_going_through_all_files"

    targetFolderForUnprocessed="${forReviewFolder}/UNPROCESSED"
    mkdir -pv "${targetFolderForUnprocessed}"

    # set nocasematch option
    shopt -s nocasematch

    currentFileCount=0
    for currentFilePath in "${sortedCompleteFilesList[@]}"; do
        process_for_given_file "$currentFilePath" "${targetFolderForUnprocessed}"

        currentFileCount=$((currentFileCount + 1))
        if (( $currentFileCount % 5000 == 0 )); then
            echo ""
            currentTime=`date +"%Y-%m-%d %H:%M:%S"`
            echo "${currentTime}: Processing status: ${currentFileCount}/${#completeFilesList[@]}"
        fi
    done

    # TODO We could remove files from the completeFilesList that we haven't processed
    # unset nocasematch option
    shopt -u nocasematch

    echo ""
    currentTime=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${currentTime}: END Processing using process_via_going_through_all_files"
}

get_all_pdf_files

sort_complete_files_list

currentTime=`date +"%Y-%m-%d %H:%M:%S"`
echo "${currentTime}: Sorted sortedCompleteFilesList: ${#sortedCompleteFilesList[@]} files."

# This turned out to be too slow.
# process_via_start_date_to_end_date

process_via_going_through_all_files

echo ""
echo ""
currentTime=`date +"%Y-%m-%d %H:%M:%S"`
echo "${currentTime}: DONE"
