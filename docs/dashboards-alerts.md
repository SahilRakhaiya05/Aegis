# SigNoz dashboards & alerts (Aegis)

Aegis emits telemetry as service **`aegis`**.

## Views

1. **Services** → `aegis`
2. **Traces** → `serviceName = aegis` and `hasError = true` after faults
3. **Logs** → `service.name = aegis`, severity ERROR
4. **Metrics** → `aegis.orders.*`, `aegis.chaos.events`, `aegis.investigations.total`

## Alerts (optional)

| Alert | Signal |
|-------|--------|
| High error rate | Trace errors for `aegis` |
| Inventory timeouts | Log contains inventory timeout |
| Investigation burst | `aegis.investigations.total` |

Deep links: UI **SigNoz** tab or `GET /api/v1/signoz/links`.
