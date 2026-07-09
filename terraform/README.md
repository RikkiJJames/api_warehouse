# Terraform: GCP project, Cloud Build, Cloud Run

Provisions a new GCP project with:
- Artifact Registry repo (`api-warehouse`) for the dbt/ingest images
- Cloud Run Jobs (`api-warehouse-dbt`, `api-warehouse-ingest`)
- Cloud Build triggers on push to `main`, which build, push, and
  `gcloud run jobs update` the corresponding job
- Secret Manager containers for DB + API creds (values NOT set by Terraform)

## Apply (three phases)

Two things can't be created by the `terraform apply` that also creates the
Cloud Run Jobs, because the jobs' `secret_key_ref`s and the repository link
are validated *at creation time*, not just at execution time:
- Cloud Run rejects job creation immediately if a referenced secret has no
  version yet — "populate secrets later" doesn't work, they must exist first.
- The GitHub connection has to exist before `google_cloudbuildv2_repository`
  can link to it.

So: project+APIs → secrets & connection → everything else.

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

3. Now populate the two things the job/repo creation depends on:

   **a. Secret values** — Terraform only creates empty containers
   (`db_secret_names` / `ingest_secret_names` in `variables.tf`). Create them
   for real, e.g. straight from your existing `.env` (values never get
   echoed/typed):
   ```
   set -a; source /path/to/.env; set +a
   for name in DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD \
     SPORTS_API_KEY SPOTIFY_CLIENT_ID SPOTIFY_CLIENT_SECRET SPOTIFY_REFRESH_TOKEN SPOTIFY_REDIRECT_URL \
     HARDCOVER_API_TOKEN TRAKT_CLIENT_ID TRAKT_CLIENT_SECRET TRAKT_REFRESH_TOKEN TRAKT_REDIRECT_URL; do
     printf '%s' "${!name}" | gcloud secrets versions add "$name" \
       --project=$(terraform output -raw project_id) --data-file=-
   done
   ```
   You'll need to run `terraform apply -target=google_secret_manager_secret.db \
   -target=google_secret_manager_secret.ingest` first if step 2 didn't already
   create the secret containers.

   **b. GitHub connection** — created out-of-band; this drives the GitHub App
   install + OAuth via Google's own OAuth client, so **no PAT is needed**:
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

4. Apply everything else — repository link, triggers, Artifact Registry,
   Cloud Run Jobs:
   ```
   terraform apply
   ```

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
