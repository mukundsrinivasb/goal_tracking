#ifndef WIFI_H
#define WIFI_H

#include "freertos/FreeRTOS.h"

// Declaration of the task function so main.c can "see" it
void wifi_task(void *pvParameters);

#endif
