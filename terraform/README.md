# Deploy resources with Terraform

## Preliminaries

- 1. Create a new Project on Google Cloud platform 
- 2. Create a Service Account that can be used to deploy resources 
    - Name = `terraform-runner`
    - Make sure it has the roles: `BigQuery Admin`, `Compute Admin`, and `Storage Admin`
    - Export the credentials file (`gcs.json`) to your local machine (DON'T SHARE IT!)
    - Transfer the credentials file to your Virtual Machine (VM):
        - On your local computer, navigate to the folder in which the `gcs.json` file is located
        - Type `sftp de-zoomcamp` to setup a FTP connection
        - Type `put gcs.json` to transfer the crendentials file
    - Create new environment variable and authenticate 
        - Create a new environment variable: `export GOOGLE_APPLICATION_CREDENTIALS=~/.gc/gcs.json`
        - Authenticate with GCloud (make sure you have the Google Cloud SDK `gcloud --version` on your VM) with: `gcloud auth activate-service-account --key-file $GOOGLE_APPLICATION_CREDENTIALS`
            - Add this command to your startup file `.bashrc` to run it automatically when starting up the VM
        - Check with `printenv` if the environment variable is set

## Deploy resources

- Navigate to your Terraform folder: `cd terraform`
- Run `terraform init` to prepare the working directory
- Run `terraform plan` to show changes required by the current configuration (what am I about to do?)
- Run `terraform apply` to create or update the infrastructure (Do what is in the tf files defined)
    - IMPORTANT: Make sure that the GOOGLE_APPLICATION_CREDENTIALS environment variable is set. Google Cloud SDK automatically recognizes this.
- Run `terraform destroy` to remove previously created infrastructure as defined in the terraform files