// main.c
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "shared_state.h"
#include "wifi.h"
#include "led.h"
#include "turso.h"
#include "esp_sntp.h"
#include <time.h>

atomic_bool g_wifi_connected = false;
atomic_bool g_tomorrow_plans_uploaded = false; // Controls the aggressive LED reminder

static void initialize_sntp(void)
{
    printf("Initializing SNTP for SSL validation...\n");
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, "pool.ntp.org");
    esp_sntp_init();

    int retry = 0;
    while (sntp_get_sync_status() == SNTP_SYNC_STATUS_RESET && ++retry < 15) {
        printf("Waiting for system time to be set... (%d/15)\n", retry);
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}

void app_main(void)
{
    // Start background tasks
    xTaskCreatePinnedToCore(wifi_task, "wifi", 4096, NULL, 5, NULL, 1);
    xTaskCreatePinnedToCore(led_task,  "led",  2048, NULL, 3, NULL, 0);

    // Wait until Wi-Fi is successfully connected
    while (!atomic_load(&g_wifi_connected)) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }

    // Sync time before validating SSL certificates
    initialize_sntp();

// Set timezone to Australian Eastern Standard/Daylight Time
setenv("TZ", "AEST-10AEDT,M10.1.0,M4.1.0/3", 1);
tzset();

// Main application loop: periodically checks plans during enforcement hours
while (1) {
    time_t now;
    time(&now);
    
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    
    // Only check tomorrow's plans between 11 PM (23) and 3 AM (3)
    bool is_check_window = (timeinfo.tm_hour >= 23 || timeinfo.tm_hour < 3);

    if (is_check_window) {
        // Calculate strictly tomorrow's date using standard calendar math
        time_t tomorrow_time = now + (24 * 60 * 60);
        if(timeinfo.tm_hour >= 0 && timeinfo.tm_hour < 3){
                tomorrow_time = now ;
            }
        struct tm tomorrow_info;
        localtime_r(&tomorrow_time, &tomorrow_info);
        
        char tomorrow[12];
        strftime(tomorrow, sizeof(tomorrow), "%Y-%m-%d", &tomorrow_info);

        printf("Enforcement window active! Checking if tomorrow's plans (%s) are uploaded...\n", tomorrow);
        char* plans_for_tomorrow = get_plans(tomorrow);
        
        if (plans_for_tomorrow != NULL) {
            if (strstr(plans_for_tomorrow, "No plans found") != NULL) {
                printf("\n--- Schedule (%s) ---\nNo plans uploaded yet.\n------------------------\n", tomorrow);
                atomic_store(&g_tomorrow_plans_uploaded, false);
            } else {
                printf("\n--- Schedule (%s) ---\n%s------------------------\n", tomorrow, plans_for_tomorrow);
                atomic_store(&g_tomorrow_plans_uploaded, true);
            }
            free(plans_for_tomorrow);
        }
        
        // Check second during the enforcement window
        vTaskDelay(pdMS_TO_TICKS(1000));
    } else {
        // Outside the enforcement window, ensure flag is clear and rest the task
        atomic_store(&g_tomorrow_plans_uploaded, true);
        
        // Check less frequently outside the window (e.g., every 30 minutes)
        vTaskDelay(pdMS_TO_TICKS(30 * 60 * 1000));
    }
}


}
