#! /usr/bin/env groovy
// bulk-file-replace.groovy

import java.nio.file.Files
import java.nio.file.FileVisitor
import java.nio.file.FileVisitResult
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest

// Args:
// 1. targetFolder
// 2. second is replacementFile for the matched file


println("Command line arguments=${this.args}")

if (this.args.size() < 2) {
    println("ERROR: Not enough arguments!")
    println("Usage: bulk-file-replace.groovy targetFolder replacementFile")
    System.exit(-1) // nonzero exit
}

String targetFolderPath = this.args[0]
String replacementFileString = this.args[1]

final String SIMPLE_PDF_PATTERN = ".*\\.[pP]{1}[dD]{1}[fF]{1}"
final String PDF_FILE_WITH_TITLE_SECTION_DATE_PATTERN = '\\w{5,7}-\\d{8}-.*?\\.[pP]{1}[dD]{1}[fF]{1}'
final String TST_PDF_FILE_WITH_TITLE_SECTION_DATE_PATTERN = 'TST\\w{2,4}-\\d{8}-.*?\\.[pP]{1}[dD]{1}[fF]{1}'

// Choose a regex pattern:
String regexPattern = SIMPLE_PDF_PATTERN

String PDF_739_MD5_HASH = "b5808604069f9f61d94e0660409616ba"
String expectedMd5Hash = PDF_739_MD5_HASH

println()
println("targetFolder=${targetFolderPath}")
println("replacementFile=${replacementFileString}")
println("regexPattern=${regexPattern}")
println("expectedMd5Hash=${expectedMd5Hash}")
println()

Closure<String> calculateMd5Hash = { Path file ->
    if (Files.isRegularFile(file)) {
        MessageDigest messageDigest = MessageDigest.getInstance("MD5")
        file.eachByte(4096) { byte[] buffer, Integer length ->
            messageDigest.update(buffer, 0, length)
        }
        return messageDigest.digest().encodeHex() as String
    }
    return null
}

class ReplacementFileWalker implements FileVisitor<Path> {
    Path replacementFile
    String expectedMd5Hash
    String fileMatchRegex
    int processedFileCount = 0
    int totalFileCount = 0

    ReplacementFileWalker(Path replacementFile, String expectedMd5Hash, String fileMatchRegex) {
        this.replacementFile = replacementFile
        this.expectedMd5Hash = expectedMd5Hash
        this.fileMatchRegex = fileMatchRegex
    }

    String calculateMd5Hash(Path file) {
        if (Files.isRegularFile(file)) {
            MessageDigest messageDigest = MessageDigest.getInstance("MD5")
            file.eachByte(4096) { byte[] buffer, Integer length ->
                messageDigest.update(buffer, 0, length)
            }
            return messageDigest.digest().encodeHex() as String
        }
        return null
    }

    @Override
    FileVisitResult preVisitDirectory(Path dirPath, BasicFileAttributes attrs) throws IOException {
        return FileVisitResult.CONTINUE
    }

    @Override
    FileVisitResult visitFile(Path filePath, BasicFileAttributes attrs) throws IOException {
        // Given a file
        if (filePath.fileName.toString() ==~ /${fileMatchRegex}/) {
            String md5Hash = calculateMd5Hash(filePath)
            if (md5Hash == expectedMd5Hash) {
                println("Replacing ${filePath} with ${replacementFile}")
                Files.copy(replacementFile, filePath, StandardCopyOption.REPLACE_EXISTING)
                processedFileCount += 1
            } else {
                println("NOT replacing ${filePath}, md5Hash=${md5Hash}")
            }
            totalFileCount += 1
        } else {
            // skip the file
        }
        return FileVisitResult.CONTINUE
    }

    @Override
    FileVisitResult visitFileFailed(Path filePath, IOException exc) throws IOException {
        return FileVisitResult.TERMINATE
    }

    @Override
    FileVisitResult postVisitDirectory(Path dirPath, IOException exc) throws IOException {
        return FileVisitResult.CONTINUE
    }
}

Path targetFolder = Path.of(targetFolderPath)
if (!Files.exists(targetFolder)) {
    throw new RuntimeException("targetFolder=${targetFolder.normalize()} must exist!")
}

Path replacementFile = Path.of(replacementFileString)
if (!Files.exists(replacementFile)) {
    throw new RuntimeException("replacementFile=${replacementFile.normalize()} must exist!")
}

ReplacementFileWalker replacementFileWalker = new ReplacementFileWalker(replacementFile, expectedMd5Hash, regexPattern)
Files.walkFileTree(targetFolder, replacementFileWalker)

println("Processed processedFileCount=${replacementFileWalker.processedFileCount} out of total=${replacementFileWalker.totalFileCount}")
