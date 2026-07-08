# Terraform: GCP project, Cloud Build, Cloud Run

Provisions a new GCP project with:
- Artifact Registry repo (`api-warehouse`) for the dbt/ingest images
- Cloud Run Jobs (`api-warehouse-dbt`, `api-warehouse-ingest`)
- Cloud Build triggers on push to `main`, which build, push, and
  `gcloud run jobs update` the corresponding job
- Secret Manager containers for DB + API creds (values NOT set by Terraform)

## Apply (two phases)

The GitHub connection is created out-of-band via `gcloud`, which needs the
project and Cloud Build API to already exist — so this is a two-step apply.

1. `gcloud auth application-default login` (Terraform runs as you). You need
   `roles/billing.user` on the target billing account and permission to
   create projects (e.g. `roles/resourcemanager.projectCreator`).

2. Fill in vars and create just the project + APIs:
   ```
   cd terraform
   cp terraform.tfvars.example terraform.tfvars   # fill in real values, don't commit
   terraform init
   terraform apply -target=google_project.this -target=google_project_service.apis
   ```

3. Create the Cloud Build <-> GitHub connection interactively — this drives
   the GitHub App install + OAuth via Google's own OAuth client, so **no PAT
   is needed**:
   ```
   gcloud builds connections create github github-connection \
     --region=<region> --project=<project_id>
   ```
   Follow the printed link in your browser once (install the GitHub App on
   `github_owner/github_repo`, authorize). Confirm it's connected:
   ```
   gcloud builds connections describe github-connection \
     --region=<region> --project=<project_id>
   ```
   It should show no pending OAuth step.

4. Apply everything else. Terraform doesn't manage the connection resource
   itself (the provider has no way to read it back without a token) — it just
   points `google_cloudbuildv2_repository.parent_connection` at the
   connection's resource path built from `github_connection_name`/`region`,
   and manages the repository link, triggers, Artifact Registry, secrets, and
   Cloud Run Jobs on top of it:
   ```
   terraform apply
   ```

## Populate secrets

Terraform only creates empty Secret Manager containers. Fill in real values
out-of-band (never put them in `.tf` files or state):

```
echo -n "the-value" | gcloud secrets versions add DB_PASSWORD \
  --project=$(terraform output -raw project_id) --data-file=-
```

Repeat for every name in `db_secret_names` / `ingest_secret_names`
(`terraform/variables.tf`). Cloud Run Jobs read `latest` automatically.

## First deploy

The Cloud Run Jobs start with a placeholder image. Push to `main` (or run the
trigger manually) to build the real image and update the job:

```
gcloud builds triggers run api-warehouse-dbt --branch=main \
  --project=$(terraform output -raw project_id)
```

Then execute it:

```
gcloud run jobs execute api-warehouse-dbt --region=$(terraform output ... region) \
  --project=$(terraform output -raw project_id)
```
