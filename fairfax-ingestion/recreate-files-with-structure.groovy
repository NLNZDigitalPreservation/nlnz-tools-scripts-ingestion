#! /usr/bin/env groovy
// recreate-files-with-structure.groovy

import java.nio.file.Files

// Args:
// 1. sourceFileListing
// 2. second is target or destination folder
// 3. third is source file filename cutoff (the point after which the directory structure is recreated)
// 3. third is sample pdf file
// 4. fourth is sample metx.xml file
// 5. fifth is sample done file
// 6. sixth is sample any other file


println("Command line arguments=${this.args}")

if (this.args.size() < 4) {
    println("ERROR: Not enough arguments!")
    println("Usage: recreate-files-with-structure.groovy sourceFileListingPath targetFolder sourceFileFilenameCutoff samplePdfFilePath sampleMetsFilePath sampleDoneFilePath sampleOtherFilePath")
    System.exit(-1) // nonzero exit
}

String sourceFileListingPath = this.args[0]
String targetFolderPath = this.args[1]
String sourceFileFilenameCutoff= this.args[2]
String samplePdfFilePath = this.args[3]
String sampleMetsFilePath = this.args[4]
String sampleDoneFilePath = this.args[5]
String sampleOtherFilePath = this.args[6]

println()
println("sourceFileListingPath=${sourceFileListingPath}")
println("targetFolderPath=${targetFolderPath}")
println("sourceFileFilenameCutoff=${sourceFileFilenameCutoff}")
println("samplePdfFilePath=${samplePdfFilePath}")
println("sampleMetsFilePath=${sampleMetsFilePath}")
println("sampleDoneFilePath=${sampleDoneFilePath}")
println("sampleOtherFilePath=${sampleOtherFilePath}")
println()

File sourceFileListing = new File(sourceFileListingPath)
if (!sourceFileListing.exists()) {
    throw new RuntimeException("sourceFileListing=${sourceFileListing.getCanonicalPath()} must exist!")
}

File targetFolder = new File(targetFolderPath)
if (!targetFolder.exists()) {
    throw new RuntimeException("targetFolder=${targetFolder.getCanonicalPath()} must exist!")
}

File samplePdfFile = new File(samplePdfFilePath)
if (!samplePdfFile.exists()) {
    throw new RuntimeException("samplePdfFile=${samplePdfFile.getCanonicalPath()} must exist!")
}

File sampleMetsFile = new File(sampleMetsFilePath)
if (!sampleMetsFile.exists()) {
    throw new RuntimeException("sampleMetsFile=${sampleMetsFile.getCanonicalPath()} must exist!")
}

File sampleDoneFile = new File(sampleDoneFilePath)
if (!sampleDoneFile.exists()) {
    throw new RuntimeException("sampleDoneFile=${sampleDoneFile.getCanonicalPath()} must exist!")
}

File sampleOtherFile = new File(sampleOtherFilePath)
if (!sampleOtherFile.exists()) {
    throw new RuntimeException("sampleOtherFile=${sampleOtherFile.getCanonicalPath()} must exist!")
}

long processedFileCount = 0

String line
sourceFileListing.withReader { reader ->
    File sourceFile
    while (line = reader.readLine()) {
        sourceFile = new File(line)
        int filenameCutoffIndex = line.indexOf(sourceFileFilenameCutoff)
        if (filenameCutoffIndex < 0) {
            println("Filename=${line} does not have a substring=${sourceFileFilenameCutoff}")
        } else {
            String pathAfterCutoff = line.substring(filenameCutoffIndex + sourceFileFilenameCutoff.length())
            //println("pathAfterCutoff=${pathAfterCutoff}")
            int filenameIndex = pathAfterCutoff.indexOf(sourceFile.getName())
            String pathAfterCutoffWithoutFilename = pathAfterCutoff.substring(0, filenameIndex)
            if (pathAfterCutoffWithoutFilename.endsWith(File.separator)) {
                pathAfterCutoffWithoutFilename = pathAfterCutoffWithoutFilename.substring(0, pathAfterCutoffWithoutFilename.size() - 1)
            }
            //println("pathAfterCutoffWithoutFilename=${pathAfterCutoffWithoutFilename}")
            File newFileParent = new File(targetFolderPath, pathAfterCutoffWithoutFilename)
            File newFile = new File(newFileParent, sourceFile.getName())
            newFileParent.mkdirs()
            if (newFile.getName().endsWith(".pdf")) {
                Files.copy(samplePdfFile.toPath(), newFile.toPath())
            } else if ("done".equals(newFile.getName())) {
                Files.copy(sampleDoneFile.toPath(), newFile.toPath())
            } else if ("mets.xml".equals(newFile.getName())) {
                Files.copy(sampleMetsFile.toPath(), newFile.toPath())
            } else {
                Files.copy(sampleOtherFile.toPath(), newFile.toPath())
            }
            processedFileCount += 1
            if (processedFileCount % 100 == 0) {
                print(".")
            }
            if (processedFileCount % 10000 == 0) {
                println()
                println("Processed ${processedFileCount} files.")
            }
        }
    }
}

println("Processed processedFileCount=${processedFileCount}")

