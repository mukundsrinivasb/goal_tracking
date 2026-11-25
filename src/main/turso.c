#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_crt_bundle.h"
#include "cJSON.h"
#include "sdkconfig.h"
#include <string.h>

static const char *TAG = "TURSO";

#define TURSO_URL "https://" CONFIG_TURSO_HOST "/v2/pipeline"
#define TURSO_AUTH_HEADER "Bearer " CONFIG_TURSO_TOKEN

typedef struct {
    char *buffer;
    int length;
} http_response_data_t;

static esp_err_t turso_http_event_handler(esp_http_client_event_t *evt) {
    http_response_data_t *res_data = (http_response_data_t *)evt->user_data;
    
    switch(evt->event_id) {
        case HTTP_EVENT_ON_HEADER:
            if (esp_http_client_get_status_code(evt->client) == 401) {
                ESP_LOGE(TAG, "Authentication failed! Check your TURSO_TOKEN in menuconfig.");
            }
            break;
        case HTTP_EVENT_ON_DATA:
            res_data->buffer = realloc(res_data->buffer, res_data->length + evt->data_len + 1);
            if (res_data->buffer == NULL) {
                ESP_LOGE(TAG, "Failed to allocate memory for output buffer");
                return ESP_FAIL;
            }
            memcpy(res_data->buffer + res_data->length, evt->data, evt->data_len);
            res_data->length += evt->data_len;
            res_data->buffer[res_data->length] = '\0';
            break;
        default:
            break;
    }
    return ESP_OK;
}

// --- DATABASE INTERFACE ---

cJSON* turso_execute_query(const char *sql, cJSON *args) {
    http_response_data_t res_data = {0};
    cJSON *json_resp = NULL;

    esp_http_client_config_t config = {
        .url = TURSO_URL,
        .event_handler = turso_http_event_handler,
        .crt_bundle_attach = esp_crt_bundle_attach,
        .user_data = &res_data,
        .transport_type = HTTP_TRANSPORT_OVER_SSL,
        .buffer_size = 4096,
        .buffer_size_tx = 4096,
    };
    
    esp_http_client_handle_t client = esp_http_client_init(&config);
    
    // 1. Construct the pipeline payload
    cJSON *root = cJSON_CreateObject();
    cJSON *requests = cJSON_CreateArray();
    cJSON_AddItemToObject(root, "requests", requests);

    cJSON *req_exec = cJSON_CreateObject();
    cJSON_AddStringToObject(req_exec, "type", "execute");
    cJSON *stmt = cJSON_CreateObject();
    cJSON_AddStringToObject(stmt, "sql", sql);
    
    if (args != NULL) {
        cJSON_AddItemToObject(stmt, "args", args);
    }
    
    cJSON_AddItemToObject(req_exec, "stmt", stmt);
    cJSON_AddItemToArray(requests, req_exec);

    cJSON *req_close = cJSON_CreateObject();
    cJSON_AddStringToObject(req_close, "type", "close");
    cJSON_AddItemToArray(requests, req_close);

    char *post_data = cJSON_PrintUnformatted(root);
    cJSON_Delete(root); // Automatically frees 'args' as well

    // 2. Execute HTTP Request
    esp_http_client_set_method(client, HTTP_METHOD_POST);
    esp_http_client_set_header(client, "Authorization", TURSO_AUTH_HEADER);
    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_post_field(client, post_data, strlen(post_data));

    esp_err_t err = esp_http_client_perform(client);

    if (err == ESP_OK && res_data.buffer != NULL) {
        json_resp = cJSON_Parse(res_data.buffer);
        if (json_resp == NULL) {
            ESP_LOGE(TAG, "Failed to parse JSON response");
        }
    } else if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error performing HTTP request: %s", esp_err_to_name(err));
    }
    
    // 3. Cleanup
    free(post_data);
    if (res_data.buffer != NULL) {
        free(res_data.buffer);
    }
    esp_http_client_cleanup(client);

    return json_resp;
}

// --- BUSINESS LOGIC IMPLEMENTATION ---

char* get_plans(const char *date) {
    char *output_str = calloc(1, 1);

    // 1. Prepare Arguments
    cJSON *args = cJSON_CreateArray();
    cJSON *arg1 = cJSON_CreateObject();
    cJSON_AddStringToObject(arg1, "type", "text");
    cJSON_AddStringToObject(arg1, "value", date);
    cJSON_AddItemToArray(args, arg1);

    // 2. Call Interface
    cJSON *json_resp = turso_execute_query("SELECT * FROM daily_plans WHERE log_date = ?", args);

    if (json_resp == NULL) {
        free(output_str);
        return strdup("Error: Failed to fetch or parse response.\n");
    }

    // 3. Process Response
    cJSON *results_arr = cJSON_GetObjectItem(json_resp, "results");
    cJSON *req_0       = cJSON_GetArrayItem(results_arr, 0);
    cJSON *resp_obj    = cJSON_GetObjectItem(req_0, "response");
    cJSON *result_obj  = cJSON_GetObjectItem(resp_obj, "result");
    cJSON *rows        = cJSON_GetObjectItem(result_obj, "rows");

    if (cJSON_IsArray(rows)) {
        int row_count = cJSON_GetArraySize(rows);
        
        if (row_count == 0) {
            free(output_str);
            output_str = strdup("No plans found for today.\n");
        }

        for (int i = 0; i < row_count; i++) {
            cJSON *row = cJSON_GetArrayItem(rows, i);
            
            cJSON *col_time = cJSON_GetArrayItem(row, 2);
            cJSON *col_task = cJSON_GetArrayItem(row, 3);

            cJSON *val_time = cJSON_GetObjectItem(col_time, "value");
            cJSON *val_task = cJSON_GetObjectItem(col_task, "value");

            const char *time_str = cJSON_IsString(val_time) ? val_time->valuestring : "N/A";
            const char *task_str = cJSON_IsString(val_task) ? val_task->valuestring : "N/A";

            char temp_buffer[256];
            snprintf(temp_buffer, sizeof(temp_buffer), "[%s] %s\n", time_str, task_str);

            char *new_str = realloc(output_str, strlen(output_str) + strlen(temp_buffer) + 1);
            if (new_str) {
                output_str = new_str;
                strcat(output_str, temp_buffer);
            }
        }
    } else {
        free(output_str);
        output_str = strdup("Error: Invalid JSON response structure.\n");
    }
    
    // 4. Cleanup parsed JSON tree
    cJSON_Delete(json_resp);
    
    return output_str;
}
