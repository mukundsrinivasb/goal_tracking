idf_component_register(SRCS "main.c" "wifi.c" "led.c" "turso.c" 
                       INCLUDE_DIRS "."
                       REQUIRES esp_driver_gpio esp_wifi esp_event nvs_flash esp_netif led_strip esp_http_client mbedtls json)
