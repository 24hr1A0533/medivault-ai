# PHASE 7: DEPLOYMENT AUDIT & INFRASTRUCTURE RELIABILITY REPORT

**System:** MediVault AI Hospital Operating System  
**Auditor:** Staff DevOps Engineer & Site Reliability Engineer (SRE)  
**Verification Date:** 2026-10-25  
**Mission Directive:** Assume nothing works. Identify every deployment failure point, orchestration flaw, container anti-pattern, and missing reliability primitive before hospital deployment.

---

## 1. Executive Summary & Assessment

| Component | Target Spec | Current Codebase State | Status | Risk Level |
| :--- | :--- | :--- | :--- | :--- |
| **Kubernetes (EKS)** | Multi-AZ Production Pods | Placeholder AWS Account ID & ECR Repo; Missing Secret/ConfigMap Env Mounts | **FAIL** | **P0 (Launch Blocker)** |
| **Terraform IaC** | Automated VPC & EKS | Dummy Subnet IDs & Mock IAM Role ARNs | **FAIL** | **P0 (Launch Blocker)** |
| **Docker Compose** | One-click Local Staging | Missing Frontend container; Missing Healthchecks; Plaintext Passwords | **FAIL** | **P1 (Critical)** |
| **Edge Ingress (Nginx)** | TLS 1.3 Terminated Ingress | Listens on Port 80 only; No SSL config despite Compose port 443 mapping | **FAIL** | **P1 (Critical)** |
| **CI/CD Pipeline** | Automated Test & Rollback | Zero `.github/workflows` or CI/CD deployment automation files in repository | **FAIL** | **P1 (Critical)** |
| **Container Images** | Multi-stage Hardened | Root execution in Dockerfile runner; missing non-root user | **FAIL** | **P2 (High)** |

---

## 2. Granular Issue Breakdown

### Issue DEP-01: Dummy ECR Image URL in Kubernetes Deployment Manifest
- **File:** [infra/kubernetes/deployment.yaml](file:///d:/medivalutAI/infra/kubernetes/deployment.yaml#L25)
- **Line:** 25
- **Priority:** **P0 (Launch Blocker)**
- **Defect Description:**  
  The pod container image is specified as:
  ```yaml
  image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/medivault/api:2.5.0
  ```
  AWS account `123456789012` is an invalid placeholder. Applying this manifest in any cluster immediately results in `ImagePullBackOff` and complete deployment failure.
- **Production-Grade Fix:**  
  Parameterize container images using Helm, Kustomize, or CI environment variables with valid ECR credentials and image tags:
  ```yaml
  image: ${ECR_REGISTRY}/medivault-api:${CI_COMMIT_SHA}
  imagePullPolicy: Always
  ```

---

### Issue DEP-02: Missing Environment Variables & ConfigMaps in Kubernetes Manifest
- **File:** [infra/kubernetes/deployment.yaml](file:///d:/medivalutAI/infra/kubernetes/deployment.yaml#L23-L48)
- **Line:** 23–48
- **Priority:** **P0 (Launch Blocker)**
- **Defect Description:**  
  The container specification does not include an `env` or `envFrom` block. Consequently, `DATABASE_URL`, `REDIS_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `JWT_SECRET_KEY`, and `TENANT_MASTER_KEY` are undefined. When pods launch, FastAPI crashes immediately during module evaluation or attempts to connect to `localhost:5432`.
- **Production-Grade Fix:**  
  Inject secrets via Kubernetes `SecretKeyRef` or AWS Secrets Store CSI driver:
  ```yaml
  envFrom:
    - configMapRef:
        name: medivault-config
    - secretRef:
        name: medivault-secrets
  ```

---

### Issue DEP-03: Hardcoded Mock Subnets & IAM Roles in Terraform
- **File:** [infra/terraform/main.tf](file:///d:/medivalutAI/infra/terraform/main.tf#L29-L36)
- **Line:** 29, 33–36
- **Priority:** **P0 (Launch Blocker)**
- **Defect Description:**  
  The EKS resource relies on mock string literals:
  ```hcl
  role_arn = "arn:aws:iam::123456789012:role/EKSClusterRole"
  subnet_ids = [
    "subnet-0a1b2c3d4e5f6g7h8",
    "subnet-0b2c3d4e5f6g7h8i9",
    "subnet-0c3d4e5f6g7h8i9j0"
  ]
  ```
  Running `terraform apply` fails during validation before creating any AWS infrastructure.
- **Production-Grade Fix:**  
  Define dynamic VPC data sources or VPC modules that generate valid subnets and create the IAM role dynamically with the required AmazonEKSClusterPolicy attachments:
  ```hcl
  module "vpc" {
    source = "terraform-aws-modules/vpc/aws"
    ...
  }
  subnet_ids = module.vpc.private_subnets
  ```

---

### Issue DEP-04: Missing Frontend Service in Root Docker Compose
- **File:** [docker-compose.yml](file:///d:/medivalutAI/docker-compose.yml#L1-L125)
- **Line:** 1–125
- **Priority:** **P1 (Critical)**
- **Defect Description:**  
  `docker-compose.yml` defines `medivault-api`, `mllp-gateway`, `postgres-db`, `redis-cache`, `kafka-broker`, `prometheus`, and `grafana`. However, it does not contain a service for the frontend client (neither `medivault-ai/frontend` Vite dev server nor an Nginx static build container). Running `docker compose up` starts backend services but leaves hospital staff with no accessible web user interface.
- **Production-Grade Fix:**  
  Add `medivault-frontend` service to `docker-compose.yml`:
  ```yaml
  medivault-frontend:
    build:
      context: ./medivault-ai/frontend
      dockerfile: Dockerfile
    container_name: medivault-frontend
    ports:
      - "5173:80"
    depends_on:
      - medivault-api
    networks:
      - medivault-net
  ```

---

### Issue DEP-05: Missing Healthcheck Probes & Dependency Conditions in Compose
- **File:** [docker-compose.yml](file:///d:/medivalutAI/docker-compose.yml#L32-L36)
- **Line:** 32–36, 55–68
- **Priority:** **P1 (Critical)**
- **Defect Description:**  
  `medivault-api` uses naive `depends_on: [postgres-db, redis-cache, kafka-broker]`. In Docker Compose v2, `depends_on` only waits for container creation, not database readiness. Because PostgreSQL and Kafka require 5–15 seconds to initialize storage and run schema migrations, `medivault-api` will encounter connection refused errors during startup and abort.
- **Production-Grade Fix:**  
  Add health checks to backing services and specify `condition: service_healthy`:
  ```yaml
  postgres-db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 5

  medivault-api:
    depends_on:
      postgres-db:
        condition: service_healthy
      redis-cache:
        condition: service_healthy
  ```

---

### Issue DEP-06: Edge Ingress Missing TLS / SSL Termination
- **File:** [infra/nginx/nginx.conf](file:///d:/medivalutAI/infra/nginx/nginx.conf#L17-L20)
- **Line:** 17–20
- **Priority:** **P1 (Critical)**
- **Defect Description:**  
  Nginx only listens on `listen 80;` and has no SSL certificate directives (`ssl_certificate`, `ssl_certificate_key`). However, `docker-compose.yml` maps `"443:443"`. If a client attempts to connect to port 443 with HTTPS, the connection is instantly rejected. Furthermore, Nginx sets the HSTS header `Strict-Transport-Security` over plaintext HTTP, violating RFC 6797 and HIPAA Security Rule 45 CFR § 164.312(e)(1) regarding transmission security.
- **Production-Grade Fix:**  
  Configure TLS 1.3 server block with Let's Encrypt / hospital corporate certificates and redirect port 80 to 443:
  ```nginx
  server {
      listen 80;
      server_name api.medivault.health;
      return 301 https://$host$request_uri;
  }
  server {
      listen 443 ssl;
      ssl_certificate /etc/ssl/certs/medivault.crt;
      ssl_certificate_key /etc/ssl/certs/medivault.key;
      ssl_protocols TLSv1.2 TLSv1.3;
      ...
  }
  ```

---

### Issue DEP-07: Container Execution as Root User
- **File:** [infra/docker/Dockerfile.api](file:///d:/medivalutAI/infra/docker/Dockerfile.api#L13-L27)
- **Line:** 13–27
- **Priority:** **P2 (High)**
- **Defect Description:**  
  The Dockerfile does not declare a `USER` directive in the runner stage. The Python process runs as Linux `root` (UID 0). In a hospital environment, a remote code execution vulnerability or container escape flaw gives an attacker root host privileges.
- **Production-Grade Fix:**  
  Create and switch to a dedicated non-root user:
  ```dockerfile
  RUN groupadd -r medivault && useradd -r -g medivault -s /sbin/nologin medivault
  USER medivault
  ```

---

### Issue DEP-08: Complete Absence of CI/CD Workflow Automations
- **File:** `.github/workflows/` (Repository Root)
- **Line:** N/A (Missing directory)
- **Priority:** **P1 (Critical)**
- **Defect Description:**  
  There is no continuous integration or continuous deployment pipeline. Pull requests are not tested automatically, linting is not enforced, Docker images are not built and scanned for CVEs (Trivy/Clair), and there is no automated rollback mechanism for failed canary deployments.
- **Production-Grade Fix:**  
  Create `.github/workflows/ci-cd.yml` defining lint, test, docker build, Trivy vulnerability scan, and ArgoCD / EKS GitOps deploy stages.
