// logger.c
#include "logger.h"

// Define the global logFile pointer
FILE *logFile = NULL;

void init_log_file(const char *filename) {
    logFile = fopen(filename, "a");
    if (logFile == NULL) {
        printf("Error opening log file: %s\n", filename);
    }
}

void log_message(const char *message) {
    if (logFile != NULL) {
        fprintf(logFile, "%s\n", message);
    }
}

void log_double(const char *label, double value) {
    char log_buffer[100];
    sprintf(log_buffer, "%s: %f", label, value);  // Format the message
    log_message(log_buffer);                      // Log the message
}

void close_log_file() {
    if (logFile != NULL) {
        fclose(logFile);
        logFile = NULL;
    }
}
