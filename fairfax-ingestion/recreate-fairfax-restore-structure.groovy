#! /usr/bin/env groovy
// recreate-fairfax-restore-structure.groovy

import java.nio.file.Files

// Args:
// 1. sourceFileListing
// 2. second is destination folder
// 3. third is sample pdf file

println("Command line arguments=${this.args}")

if (this.args.size() < 3) {
    println("ERROR: Not enough arguments!")
    println("Usage: recreate-fairfax-restore-structure.groovy sourceFileListingPath destinationFolder samplePdfFilePath")
    System.exit(-1) // nonzero exit
}

String sourceFileListingPath = this.args[0]
String destinationFolderPath = this.args[1]
String samplePdfFilePath = this.args[2]

// Sample filename: /media/sf_E_DRIVE/fairfax-RESTORE/18Q1/fairfax/WRNED1-20180328-021.pdf
String SOURCE_FILE_FILENAME_CUTOFF = "/fairfax-RESTORE/"

println("sourceFileListingPath=${sourceFileListingPath}")
println("destinationFolderPath=${destinationFolderPath}")
println("samplePdfFilePath=${samplePdfFilePath}")

File sourceFileListing = new File(sourceFileListingPath)
if (!sourceFileListing.exists()) {
    throw new RuntimeException("sourceFileListing=${sourceFileListing.getCanonicalPath()} must exist!")
}

File destinationFolder = new File(destinationFolderPath)
if (!destinationFolder.exists()) {
        throw new RuntimeException("destinationFolder=${destinationFolder.getCanonicalPath()} must exist!")
}

File samplePdfFile = new File(samplePdfFilePath)
if (!samplePdfFile.exists()) {
        throw new RuntimeException("samplePdfFile=${samplePdfFile.getCanonicalPath()} must exist!")
}

long processedFileCount = 0

String line
sourceFileListing.withReader { reader ->
    File sourceFile
    while (line = reader.readLine()) {
        sourceFile = new File(line)
        int filenameCutoffIndex = line.indexOf(SOURCE_FILE_FILENAME_CUTOFF)
        if (filenameCutoffIndex < 0) {
            println("Filename=${line} does not have a substring=${SOURCE_FILE_FILENAME_CUTOFF}")
        } else {
            String pathAfterCutoff = line.substring(filenameCutoffIndex + SOURCE_FILE_FILENAME_CUTOFF.length())
            //println("pathAfterCutoff=${pathAfterCutoff}")
            int filenameIndex = pathAfterCutoff.indexOf(sourceFile.getName())
            String pathAfterCutoffWithoutFilename = pathAfterCutoff.substring(0, filenameIndex)
            if (pathAfterCutoffWithoutFilename.endsWith(File.separator)) {
                pathAfterCutoffWithoutFilename = pathAfterCutoffWithoutFilename.substring(0, pathAfterCutoffWithoutFilename.size() - 1)
            }
            //println("pathAfterCutoffWithoutFilename=${pathAfterCutoffWithoutFilename}")
            File newFileParent = new File(destinationFolderPath, pathAfterCutoffWithoutFilename)
            File newFile = new File(newFileParent, sourceFile.getName())
            newFileParent.mkdirs()
            Files.copy(samplePdfFile.toPath(), newFile.toPath())
            processedFileCount += 1
            if (processedFileCount % 100 == 0) {
                print(".")
            }
        }
    }
}

println("Processed processedFileCount=${processedFileCount}")

