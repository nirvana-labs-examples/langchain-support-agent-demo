# Nirvana Cloud API Reference

## Base URL

```
https://api.nirvanacloud.io/v1
```

All responses are JSON. All requests must include an `Authorization` header:
```
Authorization: Bearer <api-key>
```

## Rate Limits

| Endpoint class | Limit |
|---------------|-------|
| Read (GET) | 600 requests/minute |
| Write (POST/PUT/DELETE) | 120 requests/minute |
| Bulk operations | 20 requests/minute |

On rate limit: HTTP 429 with `Retry-After` header.

## Pagination

List endpoints return paginated results:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 25,
    "total": 142,
    "total_pages": 6
  }
}
```

Pass `?page=2&per_page=50` to navigate pages.

## Common Endpoints

### VMs
```
GET    /vms                     List VMs
POST   /vms                     Create VM
GET    /vms/{id}                Get VM details
DELETE /vms/{id}                Delete VM
POST   /vms/{id}/actions/stop   Stop VM
POST   /vms/{id}/actions/start  Start VM
```

### Volumes
```
GET    /volumes                 List volumes
POST   /volumes                 Create volume
DELETE /volumes/{id}            Delete volume
POST   /volumes/{id}/attach     Attach to VM
POST   /volumes/{id}/detach     Detach from VM
```

### Snapshots
```
POST   /vms/{id}/snapshots      Take snapshot
GET    /snapshots               List snapshots
DELETE /snapshots/{id}          Delete snapshot
POST   /snapshots/{id}/restore  Restore snapshot
```

## Error Format

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "VM vm_abc123 not found",
    "request_id": "req_xyz789"
  }
}
```

Include the `request_id` when contacting support.

## Client Libraries

- Python: `pip install nirvana-cloud`
- Node.js: `npm install @nirvana-labs/sdk`
- Go: `go get github.com/nirvana-labs/nirvana-go`
- Terraform: registry.terraform.io/providers/nirvana-labs/nirvana
