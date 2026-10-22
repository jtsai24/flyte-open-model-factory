# Flyte 2 open-model factory expansion plan

## Long-term goal

Turn the hack-night experiment into a durable open-model workflow that evaluates
models, selects a candidate, launches managed fine-tuning, validates the tuned
model, and can run without a laptop.

## Target architecture

- Flyte 2 provides durable orchestration, fan-out, retries, caching, lineage,
  artifacts, and run inspection.
- Together AI provides the initial hosted open-weight inference API.
- The managed fine-tuning provider will be selected later based on supported
  models, artifact ownership, export options, cost, and API quality.
- EKS becomes the eventual always-on Flyte execution environment.
- S3 stores datasets, evaluation results, and exported model adapters or weights.
- AWS Secrets Manager stores provider credentials.
- Infrastructure is reproducible through infrastructure as code.

## Expansion stages

### 1. Establish a reliable baseline

- Turn the initial prompts into a small versioned evaluation dataset.
- Evaluate multiple hosted open-weight models in parallel.
- Record model identifiers, prompts, responses, latency, usage, errors, and cost.
- Add deterministic scoring or a clearly defined evaluation rubric.

### 2. Add managed fine-tuning

- Prepare separate training and evaluation datasets.
- Select a provider-supported base model.
- Submit an SFT or LoRA job through the selected provider's training API.
- Treat the provider training-job identifier as a durable Flyte artifact.
- Poll or await training completion without keeping a laptop process alive.
- Evaluate the tuned model against the original baseline.
- Promote the tuned model only when it passes defined quality thresholds.

### 3. Own the important artifacts

- Keep the provider-hosted model or adapter available for serving.
- Export a copy of the adapter or weights when supported.
- Store exported artifacts and versioned datasets in S3.
- Record provenance: base model, dataset version, parameters, metrics, and code version.

### 4. Move Flyte off the laptop

- Deploy Flyte 2 to a small EKS environment.
- Start with one modest worker pool because Fireworks supplies the GPU compute.
- Use remote image builds and a private container registry.
- Secure the Flyte UI and API rather than exposing cluster services directly.
- Add persistent storage, backups, monitoring, budgets, and cost alerts.
- Keep Kubernetes versions current to avoid extended-support charges.

### 5. Production-style improvements

- Add scheduled or dataset-triggered evaluations.
- Retry transient provider failures with bounded backoff.
- Add model-quality regression thresholds.
- Cache completed steps so failed runs resume without repeating successful work.
- Add notifications for failed training jobs or degraded evaluation scores.
- Document rollback and disaster-recovery procedures.

## Resume-ready project narrative

Built an AWS-hosted open-model factory using Flyte 2 on EKS. The workflow
evaluates open-weight models concurrently, selects candidates using automated
metrics, launches managed LoRA fine-tuning through a hosted provider, compares
tuned models against their baselines, and promotes successful adapters for
deployment. Datasets and exported model artifacts are versioned in S3,
credentials are managed through AWS Secrets Manager, and the infrastructure is
reproducible.

## Guardrails

- Prove each workflow stage locally before provisioning EKS resources.
- Do not provision AWS infrastructure without a written cost estimate and budget alert.
- Do not place provider API keys in source code, container images, or committed files.
- Keep fine-tuning optional until evaluation demonstrates a measurable need.
- Ask for explicit approval before builds, deployments, paid API calls, dependency
  installations, or cloud-resource creation.
