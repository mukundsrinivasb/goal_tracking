#ifndef SHARED_STATE_H
#define SHARED_STATE_H

#include <stdatomic.h>

// Global variables shared across all tasks
extern atomic_bool g_wifi_connected;
extern atomic_bool g_tomorrow_plans_uploaded;

#endif
