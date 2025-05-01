# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Bank Statement Analyzer project.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and consists of the following stages:

1. **Continuous Integration (CI)**: Run unit tests for both backend and frontend
2. **Test Environment Deployment**: Deploy the backend and frontend to Fly.io in test mode
3. **End-to-End Testing**: Run Playwright tests against the test environment
4. **Development Environment Deployment**: Deploy the backend and frontend to Fly.io in dev mode
5. **Production Environment Deployment**: Deploy the backend and frontend to Render in production mode

## Workflow Files

The CI/CD pipeline is defined in the following GitHub Actions workflow files:

- `.github/workflows/ci.yml`: Runs unit tests for both backend and frontend
- `.github/workflows/deploy-test.yml`: Deploys the backend and frontend to Fly.io in test mode
- `.github/workflows/e2e-tests.yml`: Runs Playwright tests against the test environment
- `.github/workflows/deploy-dev.yml`: Deploys the backend and frontend to Fly.io in dev mode
- `.github/workflows/deploy-prod.yml`: Deploys the backend and frontend to Render in production mode

## Environments

The CI/CD pipeline deploys to three environments:

1. **Test Environment**: Used for running end-to-end tests
   - Backend: `bank-statements-api-test.fly.dev`
   - Frontend: `bank-statements-web-test.fly.dev`
   - Database: Branched Neon database from a clean one

2. **Development Environment**: Used for development and testing
   - Backend: `bank-statements-api-dev.fly.dev`
   - Frontend: `bank-statements-web-dev.fly.dev`
   - Database: Dev database in Neon

3. **Production Environment**: Used for production
   - Backend: Deployed to Render
   - Frontend: Deployed to Render
   - Database: Production database in Render

## Required Secrets

The following secrets need to be configured in GitHub:

- `FLY_API_TOKEN`: API token for Fly.io
- `NEON_API_KEY`: API key for Neon
- `NEON_PROJECT_ID`: Project ID for Neon
- `DEV_DATABASE_URL`: Connection string for the dev database in Neon
- `RENDER_API_KEY`: API key for Render
- `RENDER_SERVICE_ID_BACKEND`: Service ID for the backend in Render
- `RENDER_SERVICE_ID_FRONTEND`: Service ID for the frontend in Render

## Workflow Triggers

- **CI**: Triggered on push to main branch and pull requests to main branch
- **Test Environment Deployment**: Triggered on push to main branch and manually
- **End-to-End Testing**: Triggered after successful test environment deployment and manually
- **Development Environment Deployment**: Triggered after successful end-to-end testing and manually
- **Production Environment Deployment**: Triggered on release publication and manually

## Containerization

Both the backend and frontend are containerized using Docker:

- Backend: `bank-statements-api/Dockerfile`
- Frontend: `bank-statements-web/Dockerfile`

## Fly.io Configuration

Both the backend and frontend have Fly.io configuration files:

- Backend: `bank-statements-api/fly.toml`
- Frontend: `bank-statements-web/fly.toml`

## Manual Deployment

You can manually trigger any of the deployment workflows from the GitHub Actions tab in the repository.

## Adding New Secrets

To add new secrets to GitHub:

1. Go to the repository settings
2. Click on "Secrets and variables" > "Actions"
3. Click on "New repository secret"
4. Enter the name and value of the secret
5. Click on "Add secret"
