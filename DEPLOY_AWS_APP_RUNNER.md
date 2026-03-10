# AWS Deployment Guide (Beginner Safe)

This guide deploys both services from GitHub to AWS App Runner with GitHub Actions:

- API service (FastAPI, port 8000)
- UI service (Streamlit, port 8501)

## 1) One-time AWS setup

1. Create two ECR repositories:
   - `startup-agent-api`
   - `startup-agent-ui`
2. Create an App Runner ECR access role (for App Runner to pull from private ECR).
   - Save ARN as GitHub secret: `APP_RUNNER_ECR_ACCESS_ROLE_ARN`
3. Create a GitHub OIDC IAM role for Actions (recommended, no long-lived AWS keys).
   - Save ARN as GitHub secret: `AWS_GITHUB_OIDC_ROLE_ARN`
4. Ensure this IAM role can:
   - push images to ECR
   - call `apprunner:CreateService`, `apprunner:UpdateService`, `apprunner:ListServices`

## 2) GitHub repository secrets

In GitHub repo -> Settings -> Secrets and variables -> Actions -> New repository secret.

Required secrets:

- `AWS_GITHUB_OIDC_ROLE_ARN`
- `APP_RUNNER_ECR_ACCESS_ROLE_ARN`
- `GROQ_API_KEY`
- `TAVILY_API_KEY`
- `LANGSMITH_API_KEY` (optional; keep empty if not using LangSmith)
- `API_BASE_URL` (for UI deployment; set after API is deployed, e.g. `https://xxxx.ap-south-1.awsapprunner.com`)

Recommended repo variables:

- `AWS_REGION` = `ap-south-1`
- `ECR_API_REPOSITORY` = `startup-agent-api`
- `ECR_UI_REPOSITORY` = `startup-agent-ui`
- `APP_RUNNER_API_SERVICE_NAME` = `startup-agent-api`
- `APP_RUNNER_UI_SERVICE_NAME` = `startup-agent-ui`

## 3) First deployment order

1. Push to `main` (or manually run workflow) for API:
   - workflow: `.github/workflows/cd-api-apprunner.yml`
2. Wait until API service is created and running in App Runner.
3. Copy API public URL from App Runner.
4. Set GitHub secret `API_BASE_URL` to that API URL.
5. Push to `main` (or manually run workflow) for UI:
   - workflow: `.github/workflows/cd-ui-apprunner.yml`

## 4) Verification

After API deploy:
- open `https://<api-url>/health`
- open `https://<api-url>/health/rag`

After UI deploy:
- open UI public URL from App Runner
- run one query and confirm output is returned

## 5) How updates work

- Push API code -> API workflow rebuilds image, pushes to ECR, updates App Runner service.
- Push UI code -> UI workflow rebuilds image, pushes to ECR, updates App Runner service.

## 6) Common failures and fixes

- `AccessDenied` in GitHub Action:
  - OIDC role policy is missing ECR/App Runner permissions.
- `Missing required secret`:
  - add the missing secret in GitHub Actions settings.
- UI cannot call API:
  - `API_BASE_URL` is wrong or missing `/query` path base.
- Slow first request:
  - model cold start; this is normal for first run.
