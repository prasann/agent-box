# Local coding-agent telemetry plan

Status: planned, not installed. Each machine will run its own independent stack.
Docker is allowed; observability components must be open source and self-hosted.
No cloud backend, proprietary observability service, or prompt/code capture.

## Clean baseline

The unfinished branch-attribution hook and its emitting script have been removed.
Notification hooks, personal skills, agents, and their user-level symlinks remain.
On the current machine, Insiders OTel export and content capture are explicitly
disabled and the stale endpoint/exporter overrides are removed. Restart the
editor and existing agent sessions to apply the disabled configuration.

No telemetry backend has been installed or started. Existing logs, settings
backups, and the historical [old-Mac snapshot](../setup-in-old-mac.md) are preserved.
That snapshot is historical evidence, not the current installation procedure.
The installer does not disable telemetry in other checkouts or on other machines.

## Target architecture

```text
VS Code Stable / Insiders       Copilot CLI
             \                  /
              native OTel export
                       |
           loopback-only OTLP receiver
           OpenTelemetry Collector
           (filter, normalize, batch)
                  /           \
       approved metrics     approved traces
            Prometheus          Tempo
                  \           /
                   Grafana OSS
```

Use the OSS editions of Grafana, Tempo, Prometheus, and the OpenTelemetry
Collector. Verify licenses, release tags, and actual container artifacts before
pinning versions. Do not select Grafana Enterprise images. Docker Desktop is an
accepted host dependency, not an observability service.

Keep the first iteration small: no Loki, custom branch-mapping service, custom
web application, cloud forwarding, or fleet-wide aggregation. Logs are not an
ingestion requirement for the initial dashboards; reject/drop that signal.

## Implementation sequence

### 1. Confirm installed-client capabilities

- Record VS Code/extension and Copilot CLI versions and selected harnesses.
- Confirm each client's native export settings, protocol, schema, and restart
  requirements. CLI and editor configuration must be handled independently.
- Verify repository/branch attributes in actual metadata-only traces for each
  client. Do not assume the old hook is necessary or native attribution universal.
- Resolve the transport discrepancy before enabling export: current shared-runtime
  documentation warns that plain HTTP disables export, while extension examples
  still use localhost HTTP. Prefer a trusted local HTTPS Collector receiver where
  required. Do not disable certificate validation.

### 2. Add a reproducible, opt-in stack

- Add version-pinned Docker Compose and service configuration under a dedicated
  telemetry directory in this repository. Do not overload the symlink installer.
- Provision Grafana data sources and dashboard JSON through source control.
- Provide explicit setup, start, stop, status, and verification commands.
- Bind published ports to `127.0.0.1`, not all interfaces. Keep Grafana login enabled
  and generate a local password rather than retaining default credentials.
- Keep credentials, TLS keys, databases, and generated environment files outside
  Git, using protected per-machine storage or named Docker volumes.
- Keep product analytics and cloud exporters disabled. Review outgoing telemetry
  behavior of the selected images; local ingestion must not forward agent data.
- Generate local certificates and authentication material only during explicit
  setup. Any operating-system trust changes require user approval.
- Persist data across container restarts. Default to manual startup, not login-time
  background services. Stop commands must preserve data.

### 3. Enforce metadata-only collection

- Explicitly disable content and identity capture in every configured client;
  remove the current legacy `captureContent: true` behavior from future setup.
- Collect only approved metadata: model, token counts, cache usage, durations,
  operation/tool names, outcome, and opaque trace/session identifiers.
- Make repository/branch labeling an explicit, reviewed choice. Never retain
  credential-bearing remote URLs or full workspace paths.
- Use a Collector allowlist, not just a list of known sensitive fields to remove.
  Drop prompt/response bodies, system instructions, tool schemas, arguments and
  results, source/file content, free-text error messages, and exception payloads.
  Apply filtering to span events, resource attributes, and metric dimensions too.
- Preserve error counts and classifications without storing arbitrary error text.
- Do not enable debug exporters or log raw OTLP bodies.
- Verify disabled data classes against captured output before admitting real work.

### 4. Build useful, correctly scoped dashboards

- Sessions, model calls, and tool calls over time.
- Input/output/cache token usage and model mix.
- Model latency and time to first token/chunk, where emitted.
- Tool latency, failure rates, and subagent trace structure.
- Client-specific panels when shared attributes are not available.
- Normalize legacy `copilot_chat.*` and current `github.copilot.*` signals only
  where equivalent. Verify duration units before combining series.
- Count model tokens on `chat` spans, not both parent rollups and their children.
  Do not add cached-input subsets to input totals.
- Use native metrics where suitable; explicitly configure trace-derived metrics
  where needed. A trace attribute does not automatically become a Prometheus metric.
- Token counts and billing multipliers are not monetary spend. Do not present
  estimated costs as actual Copilot invoices.

The Microsoft Azure coding-agent dashboards use Application Insights/KQL queries.
Do not import them unchanged into the local Prometheus/Tempo stack.

### 5. Bound retention and resource use

- Start with a proposed seven-day retention for metrics and traces; make the
  selected value visible in setup documentation.
- Configure Docker resource limits, service retention, log rotation, and disk-use
  visibility. Verify cleanup rather than assuming a mounted volume bounds growth.
- Measure idle and representative-session memory/CPU on this Mac before treating
  the stack as suitable for daily use.
- Document backup and explicitly destructive reset procedures separately from
  ordinary stop/update commands.

### 6. Validate before switching telemetry on permanently

- Start from a clean per-machine install; verify readiness, not just running
  container processes.
- Send a synthetic metadata-only trace and metric, then query them through the
  actual Grafana data sources.
- Test that forbidden content attributes/events are dropped with harmless
  synthetic markers. Do not use real prompts or code as privacy test payloads.
- Run one known-size session per configured client in an unrelated repository.
  Verify client/source attribution, token totals, duration units, tool errors,
  and connected subagent spans where supported.
- Restart the stack and confirm history survives.
- Test collector downtime: clients remain usable and export failures are
  diagnosable without silently claiming successful collection.
- Re-run setup to verify idempotence; test stopping and rolling back without
  deleting data.

## Completion criteria

The revival is complete only when real editor and CLI sessions appear in the
local dashboards, persisted metadata survives restart, forbidden content is
absent, and a second-machine installation can be reproduced from the committed
configuration. During implementation, enable export only for controlled
verification; leave it disabled between tests until these criteria pass.

## References

- [VS Code monitoring guide](https://code.visualstudio.com/docs/agents/guides/monitoring-agents)
- [Shared Copilot OTel reference](https://docs.github.com/en/copilot/reference/enterprise-administrators/opentelemetry-reference)
- [Grafana development LGTM bundle](https://grafana.com/docs/opentelemetry/docker-lgtm/)
- [Microsoft's Azure-backed coding-agent dashboards](https://learn.microsoft.com/en-us/azure/managed-grafana/grafana-opentelemetry-app-insights)

The LGTM bundle is a useful development reference, not a production deployment
blueprint. The proposed stack must still configure privacy, authentication,
retention, and persistence explicitly.
