// logger.c
#include "logger.h"

// Define the global logFile pointer
FILE *logFile = NULL;

void init_log_file(const char *filename) {
    // clear
    FILE *tempFile = fopen(filename, "w");
    if (tempFile == NULL) {
        printf("Error clearing log file: %s\n", filename);
        return;
    }
    fclose(tempFile);

    // append
    logFile = fopen(filename, "a");
    if (logFile == NULL) {
        printf("Error opening log file for appending: %s\n", filename);
    }
}

void log_message(const char *message) {
    if (logFile != NULL) {
        fprintf(logFile, "%s\n", message);
    }
}

void log_double(const char *label, double value) {
    char log_buffer[100];
    sprintf(log_buffer, "%s: %e", label, value);  // Use %e to format the value in scientific notation
    log_message(log_buffer);                      // Log the message
}

void close_log_file() {
    if (logFile != NULL) {
        fclose(logFile);
        logFile = NULL;
    }
}
