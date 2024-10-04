// logger.h
#ifndef LOGGER_H
#define LOGGER_H

#include <stdio.h>

extern FILE *logFile;

void init_log_file(const char *filename);
void log_message(const char *message);
void log_double(const char *label, double value);
void close_log_file();

#endif
