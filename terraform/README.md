# Terraform: GCP project, Cloud Build, Cloud Run

Provisions a new GCP project with:
- Artifact Registry repo (`api-warehouse`) for the dbt/ingest images
- Cloud Run Jobs (`api-warehouse-dbt`, `api-warehouse-ingest`)
- Cloud Build triggers on push to `main`, which build, push, and
  `gcloud run jobs update` the corresponding job
- Secret Manager containers for DB + API creds (values NOT set by Terraform)

## One-time manual prerequisites

1. `gcloud auth application-default login` (Terraform runs as you).
2. You need `roles/billing.user` on the target billing account and permission
   to create projects (e.g. `roles/resourcemanager.projectCreator`).
3. Install the [Google Cloud Build GitHub App](https://github.com/apps/google-cloud-build)
   on `github_owner/github_repo`. Grab the installation ID from the URL at
   `github.com/settings/installations/<ID>`.
4. Create a classic GitHub PAT with `repo` scope — used once to bootstrap the
   Cloud Build <-> GitHub connection, passed as `github_token`.

## Apply

```
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in real values, don't commit
terraform init
terraform apply
```

After apply, check the GitHub connection — it often needs one more manual
OAuth click the first time:

```
terraform output cloudbuild_connection_status_check   # prints the gcloud command
```

If the connection is `PENDING_USER_OAUTH`, open the `actionUri` it prints and
finish the flow in your browser once. Re-run `terraform apply` afterwards if
the repository/trigger resources failed to create.

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
