# CrowdStrike

Query CrowdStrike Identity Protection sensors and aggregates through the
Falcon API (`api.crowdstrike.com` and region-specific hosts). Search the
sensor fleet with Falcon Query Language, pull detailed records by device
ID, and run documented aggregate queries.

## Authentication

CrowdStrike uses the Falcon API OAuth2 **client-credentials** flow. Each
action first exchanges the client ID + client secret for a short-lived
bearer token at `POST https://api.{cloud}.crowdstrike.com/oauth2/token`,
then calls the Identity Protection endpoint.

### API Key

- In the Falcon console open **Support and resources → API clients and
  keys** and create an API client.
- Grant it the Identity Protection read scopes (Identity Protection
  Entities: Read, Identity Protection Sensor: Read).
- Copy the **Client ID** and **Client Secret**.
- Provide the **Client Secret** as the API key
  (`CROWDSTRIKE_CLIENT_SECRET`). The **Client ID** and the **cloud
  region** (`us-1`, `us-2`, `eu-1`, `us-gov-1`, `us-gov-2`) are passed as
  action parameters, not stored as credentials.

There is no standalone credential-test endpoint: validating the
credential requires both the client ID and client secret together, which
are not both available at credential-test time, so verification happens
on the first action call.

## Tools

| name | description | required params |
| --- | --- | --- |
| `query_sensors` | Search Identity Protection sensors by FQL filter | `client_id`, `cloud` |
| `get_sensor_details` | Get sensor records for a list of device IDs | `client_id`, `cloud`, `ids` |
| `get_sensor_aggregates` | Run a documented sensor aggregate query | `client_id`, `cloud`, `aggregate_query` |

Every tool also takes an `api_key` parameter (the Falcon client secret)
that the runtime fills in from the resolved credential.

## Limits & Quotas

- **Token lifetime**: Falcon OAuth2 access tokens expire after ~30
  minutes; each action requests a fresh token, so no token caching is
  required.
- **Cloud region**: pick the host that matches your Falcon tenant
  (`us-1` → `api.crowdstrike.com`, `us-2` → `api.us-2.crowdstrike.com`,
  `eu-1` → `api.eu-1.crowdstrike.com`, GovCloud variants for
  `us-gov-1`/`us-gov-2`).
- **`get_sensor_details`** accepts up to 5000 device IDs per call.
- **Error model**: non-2xx responses (including auth failures) and
  timeouts are caught and returned as `success=False` + `error` rather
  than raising. Plan for retries on the agent side based on the error
  string.

## Maintainer

ModuleX core team.
