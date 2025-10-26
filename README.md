# thomas-dashlane


## 1. Setup Instructions

1. **Create a local `.env` file** with the following snowflake variables
```text
USERNAME=
SNOWFLAKE_ACCOUNT=
ROLE=
WAREHOUSE=
PASSWORD=
``` 

2. **Run the following commands to set up the virtual environment, install dbt and run models:**
```bash
make venv-setup
make dbt
```

3. **Run the exploratory data analysis with this command: `run_logistic_regression_model`** <br>
The `--impact-threshold` (`-it`) flag can be used to set the minimum impact threshold for features to be included in the output. <br> 
The default value is 1.2 (20% increase in odds). <br>
Example usage:
```bash
run_logistic_regression_model -it 1.3
``` 


## 2. Ingestion 
The data for this take home assignment consist in two static csv files. <br> 
Since they are static files they have been manually uploaded to Snowflake and are accessible through the `raw` schema: 
- `raw.events`
- `raw.user_attributes`


## 3. Modeling

All the modeling is happening in the `dbt/` folder. <br>
Models architecture have been designed with these two principles in mind:
1. Build appropriate model to answer the assignment questions
2. Build modular and reusable models, following dbt best practices. Ideally we would like to be able to leverage intermediate models for a variety of use cases, not only for the current assignment questions.

<img width="1673" height="460" alt="image" src="https://github.com/user-attachments/assets/af117696-86eb-4be7-ab85-93166578b401" />

Every dbt model has a `.yml` description file that contains information about the model, its purpose and its tests. <br>



* **[Staging models](https://github.com/ThomasCouz/thomas-dashlane/tree/main/dbt/models/staging)**
    - `stg_events`: cleans and prepares the `raw.events` table
    - `stg_user_attributes`: cleans and prepares the `raw.user_attributes` table

* **[Intermediate models](https://github.com/ThomasCouz/thomas-dashlane/tree/main/dbt/models/intermediate)**
    - `int_date.sql`: creates a date dimension table
    - `int_daily_user_events`: aggregates user events at the daily level. See next section below for more details.
    - `int_users_f7d_features_usage`: created from `int_daily_user_events`, this model selects only the first 7 days 
of user's activity events and computes features usage metrics at the user grain.

* **[Marts models](https://github.com/ThomasCouz/thomas-dashlane/tree/main/dbt/models/marts)**
  - `dim_users`: final users dimension table to be used in external systems (BI tools, reverse ETL, ML models, etc)
  - `fact_events`: final events fact table to be used in external systems (BI tools, reverse ETL, ML models, etc)
  - `fact_daily_user_events`: final daily user events fact table to be used in external systems (BI tools, reverse ETL, ML models, etc)
  - `dim_user_early_engagement`: final model used to answer the assignment questions. This model combines user attributes from `stg_user_attributes` with features usage metrics computed in `int_users_f7d_features_usage`

<br> 

**Focus on [int_daily_user_events](https://github.com/ThomasCouz/thomas-dashlane/blob/main/dbt/models/intermediate/int_daily_user_events.sql) model:** <br>
The goal with this model is to have a standard aggregation at the daily and user level that can be reused for a variety of use cases. <br>
* **Grain**: one row per user per day, between user creation date and a default end date (set as a dbt variable). In production this default end date should be the current date. 
    Note that there will be a row in this model even if the user has not triggered any event on that day <br>
* **Materialization**: this is a time series model with past data that won't change. Therefore, it is materialized as an incremental model for performance reasons. <br>
* **Late-arriving data handling**: they are accounted for in this model by setting the `lookback_window_days` variable (currently set at 2 days). This means that when the model is run, it will always recompute the last 2 days of data to capture any late-arriving events. <br>
* **Optimization**: a clustering key has been added on the `reporting_date` column to optimize queries filtering on date ranges. <br>
* **Code readability**: to improve code readability, jinja templating has been used to declare columns for every event name. The list of all events evaluated can be found in the macro `events_list.sql` <br>



## 4. Exploratory Data Analysis (EDA)

1. `dim_user_early_engagement` is the model used to identify retention drivers in early engagement. Here is the list of features in this model:
    * `creation_app_platform`: app platform used to create the user account (ios, android, web)
    * `has_<event_name>_f7d`: binary feature indicating whether the user has triggered the specific event in the first 7 days after account creation. This feature exist for all event names.
    * `cnt_days_<event_name>_f7d`: count of distinct days the user has triggered the specific event in the first 7 days after account creation. This feature exist for all event names.
    * `cnt_<event_name>_events_f7d`: total count of times the user has triggered the specific event in the first 7 days after account creation. This feature exist for all event names.
    * `is_retained_4_weeks`: binary target variable indicating whether the user has successfully converted.

2. Using this model, a **[Snowflake dashboard](https://app.snowflake.com/klvflsf/aq34769/#/dashlane-retention-drivers-in-early-engagement-dOp2eFDsq)** has been created to visualize feature importance and distribution of key features between retained and non-retained users. <br>

<img width="1619" height="1278" alt="image (2)" src="https://github.com/user-attachments/assets/2e1ab398-f6da-4b26-9675-266e3df3a52f" />

<br> <br>

3. In addition to the snowflake dashboard, a **[logistic regression model](scripts/eda/logistic_regression_model.py)** has been implemented to quantify the impact of early engagement features on 4-weeks retention. <br>
   The output of the model is a list of features that have a high Odds Ratio (meaning that increasing the feature variable by one unit have high chances of changing the outcome which is the 4-week user retention). <br>

    Here are the results of the `run_logistic_regression_model` command:
    ```text
                                           Feature      Odds Ratio
                         CREATION_APP_PLATFORM_web        2.055154
                   CNT_DAYS_LOG_IN_TO_DASHLANE_F7D        2.011771
            CNT_DAYS_ADD_NEW_PASSWORD_TO_VAULT_F7D        1.928815
      CNT_DAYS_ADD_NEW_PAYMENT_METHOD_TO_VAULT_F7D        1.441670
                 HAS_ADD_NEW_PASSWORD_TO_VAULT_F7D        1.365276
        HAS_ADD_NEW_PERSONAL_DOCUMENT_TO_VAULT_F7D        1.280242
                          HAS_PERFORM_AUTOFILL_F7D        1.244185
    CNT_ADD_NEW_PAYMENT_METHOD_TO_VAULT_EVENTS_F7D        1.196802
    ```

