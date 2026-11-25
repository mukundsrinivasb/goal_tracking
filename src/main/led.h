#ifndef LED_H
#define LED_H

#define LED_PIN        48
#define LED_NUM_PIXELS 1   // only one RGB pixel on the board

/**
 * @brief FreeRTOS task that manages the status LED indicator.
 * * Initializes the RMT peripheral for the WS2812 LED and enters a continuous loop.
 * It polls the global Wi-Fi connection state and blinks the LED accordingly 
 * (e.g., green for connected, red for disconnected).
 * * @param pvParameters Pointer to task parameters (typically passed as NULL).
 */
void led_task(void *pvParameters);

#endif
