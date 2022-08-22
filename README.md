# DataDog monitors to Helm operators

## How to use
1. Install requirements
   ```shell
   pip install -r requirements.txt
   ```

2. Create .env file on root folder with **API_KEY** and **APP_KEY** from [DataDog](https://docs.datadoghq.com/account_management/api-app-keys/)
   ```env
   API_KEY="<api_key_datadog>"
   APP_KEY="<app_key_datadog>"
   ```

3. Execute script
   ```shell
   python3 convert_monitor.py -s <service_name>
   ```

## Utils links
* [DataDog operator](https://github.com/DataDog/datadog-operator/blob/main/docs/datadog_monitor.md)