# Terraform: GCP project, Cloud Build, Cloud Run, Workflows

Provisions a new GCP project with:
- Artifact Registry repo (`api-warehouse`) for the dbt/ingest images
- Cloud Run Jobs (`api-warehouse-dbt`, `api-warehouse-ingest`)
- Cloud Build triggers on push to `main`, which build, push, and
  `gcloud run jobs update` the corresponding job
- A Workflow (`ingest-then-dbt`) that runs the ingest job, then the dbt job
  once ingest actually completes, fired hourly by Cloud Scheduler
- Secret Manager containers for DB + API creds (values NOT set by Terraform)

## Apply

Some resources can't be created on the first pass — Cloud Run rejects a job
whose secret refs have no version yet, and the repository link needs the
GitHub connection to already exist — both of those are set up out-of-band via
`bootstrap.sh`, not Terraform. In practice this is a 3-step loop, and it's
fine to just let step 1 partially fail:

1. `gcloud auth application-default login` (Terraform runs as you). You need
   `roles/billing.user` on the target billing account and permission to
   create projects (e.g. `roles/resourcemanager.projectCreator`).

2. Fill in vars and apply:
   ```
   cd terraform
   cp terraform.tfvars.example terraform.tfvars   # fill in real values, don't commit
   terraform init
   terraform apply
   ```
   This creates the project, APIs, IAM bindings, Artifact Registry, the
   Cloud Run runtime SA, and empty secret containers — then errors on the
   repository link and both Cloud Run Jobs (and skips the Workflow/Scheduler,
   which depend on the jobs). That's expected.

3. Run the bootstrap script — pushes real secret values from `.env`, then
   drives the Cloud Build <-> GitHub connection setup (GitHub App install +
   OAuth via Google's own OAuth client, **no PAT needed**):
   ```
   ./bootstrap.sh
   ```
   It reads `project_id`/`region`/`github_owner`/`github_repo` straight out
   of `terraform.tfvars` — override any of them with flags if needed
   (`./bootstrap.sh --project other-id`). If the connection prints
   `PENDING_USER_OAUTH`, open the `actionUri` from its `describe` output in a
   browser once and confirm it before moving on.

4. Apply again — repository link, triggers, both Cloud Run Jobs, the
   Workflow, and the hourly Scheduler job all create cleanly now:
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
