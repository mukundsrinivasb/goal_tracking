#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "led_strip.h"
#include "shared_state.h"
#include "led.h"
#include <time.h>

// You will need to add this to your shared_state.h and initialize it in main.c
extern atomic_bool g_tomorrow_plans_uploaded;

#define BLINK_COUNT        3
#define BLINK_ON_MS        200
#define BLINK_OFF_MS       200
#define STATUS_INTERVAL_MS 5000

static led_strip_handle_t s_led_strip;

static void led_init(void)
{
    led_strip_config_t strip_config = {
        .strip_gpio_num = LED_PIN,
        .max_leds = LED_NUM_PIXELS,
    };

    led_strip_rmt_config_t rmt_config = {
        .resolution_hz = 10 * 1000 * 1000, // 10MHz
        .flags.with_dma = false,           // Set true if you encounter flickering
    };

    ESP_ERROR_CHECK(led_strip_new_rmt_device(&strip_config, &rmt_config, &s_led_strip));
    led_strip_clear(s_led_strip);
}

static void set_color(uint8_t r, uint8_t g, uint8_t b)
{
    led_strip_set_pixel(s_led_strip, 0, r, g, b);
    led_strip_refresh(s_led_strip);
}

static void blink_color(uint8_t r, uint8_t g, uint8_t b, int count)
{
    for (int i = 0; i < count; i++) {
        set_color(r, g, b);
        vTaskDelay(pdMS_TO_TICKS(BLINK_ON_MS));
        led_strip_clear(s_led_strip);
        led_strip_refresh(s_led_strip);
        vTaskDelay(pdMS_TO_TICKS(BLINK_OFF_MS));
    }
}

void led_task(void *pvParameters)
{
    led_init();
    while (1) {
        // 1. Get current local time
        time_t now;
        struct tm timeinfo;
        time(&now);
        localtime_r(&now, &timeinfo);
        
        // Active from 11:00 PM (23) until 3:59 AM
        bool is_enforcement_time = (timeinfo.tm_hour >= 23 || timeinfo.tm_hour < 4);
        bool plans_uploaded = atomic_load(&g_tomorrow_plans_uploaded);

        // 2. Evaluate State
        if (is_enforcement_time && !plans_uploaded) {
            // AGGRESSIVE REMINDER: Obnoxious, rapid Red/Green strobing
            set_color(255, 0, 0); // Pure Red
            vTaskDelay(pdMS_TO_TICKS(75));
            set_color(0, 255, 0); // Pure Green
            vTaskDelay(pdMS_TO_TICKS(75));
        } else if (plans_uploaded) {
            // Goal achieved: Go dark, let the user sleep
            led_strip_clear(s_led_strip);
            led_strip_refresh(s_led_strip);
            vTaskDelay(pdMS_TO_TICKS(2000));
        } else {
            // It is AM and plans aren't uploaded yet: Normal Wi-Fi status
            if (atomic_load(&g_wifi_connected)) {
                blink_color(20, 50, 0, 1);
                vTaskDelay(pdMS_TO_TICKS(STATUS_INTERVAL_MS));
            } else {
                blink_color(255, 0, 0, 1);
                vTaskDelay(pdMS_TO_TICKS(1000));
            }
        }
    }
}
