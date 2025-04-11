# Ticketmaster Event Extracter (TEE)

## Repo Structure

```
/ticketmaster-de-pipeline
│
├── /terraform            # Directory for Terraform configuration files
│   ├── main.tf           # Main configuration file for Terraform
│   ├── variables.tf      # Variables used within Terraform configurations
│   ├── outputs.tf        # Define outputs from Terraform operations
│   └── README.md         # Documentation for setting up infrastructure
│
├── /docker               # Directory for Docker-related files
│   ├── Dockerfile        # Dockerfile to build the environment
│   ├── requirements.txt  # List of Python dependencies
│   └── README.md         # Documentation for building and managing Docker container
│
├── /src                  # Source code directory
│   ├── extract_data.py   # Script to extract data from Ticketmaster API
│   ├── load_to_gcp.py    # Script to load data into Google Cloud storage
│   ├── load_to_bq.py     # Script to load data from storage to BigQuery
│   └── __init__.py       # Python package file
│
├── /kestra               # Kestra workflow configurations
│   ├── workflow.yaml     # Kestra workflow definition file
│   └── README.md         # Documentation for orchestrating tasks with Kestra
│
├── /dashboard            # Directory for Metabase dashboard configurations
│   └── README.md         # Documentation for visualizing data in Metabase
│
├── .gitignore            # File specifying files to ignore in version control
├── README.md             # Main documentation for project overview, setup, and usage
└── LICENSE               # License file (if applicable)
```


## References

Articles:
- https://medium.com/geekculture/airflow-vs-prefect-vs-kestra-which-is-best-for-building-advanced-data-pipelines-40cfbddf9697