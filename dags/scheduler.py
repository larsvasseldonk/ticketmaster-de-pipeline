from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


# from src.extract_data import extract_data
# from src.load_to_gcs import load_to_gcs
# from src.load_to_bq import load_to_bq

# Define default arguments
default_args = {
    'owner': 'airflow',
    'start_date': datetime.now(),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='ticketmaster_to_bigquery_pipeline',
    default_args=default_args,
    description='A simple DAG to extract data from Ticketmaster API and load it into BigQuery',
    schedule_interval='0 0 * * *',  # Daily at midnight
    catchup=False,
    is_paused_upon_creation=False,
) as dag:
    
    task1 = BashOperator(
        task_id='extract_data',
        bash_command='python ../src/extract_data.py',
    )

    task2 = BashOperator(
        task_id='load_to_gcs',
        bash_command='python ../src/load_to_gcs.py',
    )
    # task3 = BashOperator(
    #     task_id='load_to_bq',
    #     bash_command='python load_to_bq.py',
    # )

# Define task dependencies
task1 >> task2 #>> task3