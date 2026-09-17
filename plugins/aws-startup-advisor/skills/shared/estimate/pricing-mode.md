# Estimate — Pricing Mode Selection (canonical Step 0)

> Canonical pricing-mode procedure for estimate cost engines, vendored into
> each skill (`references/vendored/estimate/pricing-mode.md`) and kept
> byte-identical by `shared:sync`. The `cached_stale` enum bug happened because
> two copies of this logic evolved separately — do not fork this text again.
> Skill cost engines execute this file AS their Step 0, then own everything
> after it (baseline rungs, service formulas, tiers).

## Step 0a: Load the pricing cache

Read `references/vendored/pricing/aws-infra-pricing.json`. Check
`_meta.last_updated` against `_meta.staleness_days` (default 30):

- Within the window: **cached prices are the primary source.** No MCP calls
  needed for services in the file. Set `pricing_source: "cached"`.
- Past the window: infrastructure prices remain reliable. Attempt MCP (Step
  0b) for services not in the file; use cached rates as fallback with
  `pricing_source: "cached_stale"`.

Each service object carries its rates and (where relevant) a
`multi_az_handling` key. Look rates up from the file — never hardcode them.

## Step 0b: MCP availability check (only if cache stale or service not listed)

Live pricing comes from the AWS Price List API, reached through the AWS MCP
server's `aws___run_script` tool via `call_boto3`. Attempt it with **up to 2
retries** (3 total attempts, 10-second timeout per attempt):

1. Attempt 1: a `pricing.DescribeServices` probe (see the canonical call below)
2. Timeout/error → wait 1s, attempt 2
3. Timeout/error → wait 2s, attempt 3
4. All 3 fail → cached prices, `pricing_source: "cached_fallback"`

The probe doubles as the credential check: the Price List API needs
`pricing:DescribeServices` / `pricing:GetProducts`, so an `AccessDenied` or a
missing-credential error is a failed attempt, not a retryable one — go straight
to `cached_fallback` rather than burning the remaining retries.

### Canonical Price List calls

All pricing goes through `aws___run_script`. `region_name` selects the **API
endpoint**, which only exists in `us-east-1`, `eu-central-1`, and
`ap-south-1` — it is **not** the region being priced. The region being priced is
always a `regionCode` filter. Passing the user's target region as `region_name`
is the one mistake to avoid here: it either fails to connect or silently prices
the wrong thing.

```python
# Availability probe / service-code enumeration
call_boto3(service_name="pricing", operation_name="DescribeServices",
           region_name="us-east-1")

# Attribute names available for a service code
call_boto3(service_name="pricing", operation_name="DescribeServices",
           region_name="us-east-1", params={"ServiceCode": "AmazonEC2"})

# Allowed values for one attribute
call_boto3(service_name="pricing", operation_name="GetAttributeValues",
           region_name="us-east-1",
           params={"ServiceCode": "AmazonEC2", "AttributeName": "instanceType"})

# A unit price. `regionCode` is the region being priced.
call_boto3(service_name="pricing", operation_name="GetProducts",
           region_name="us-east-1",
           params={"ServiceCode": "AmazonEC2", "Filters": [
               {"Type": "TERM_MATCH", "Field": "regionCode", "Value": "<target region>"},
               {"Type": "TERM_MATCH", "Field": "instanceType", "Value": "m7g.large"},
           ]})
```

`GetProducts` returns `PriceList` as a list of **JSON strings** — parse each
before reading `terms.OnDemand`. Ask the script to return only the extracted
unit rate, not the raw payload; a single unfiltered `GetProducts` response can
run to megabytes.

## Step 0c: Display the pricing mode

Before any calculation, surface the status:

- Cache fresh + all services covered: "Pricing source: cached (updated
  [date], ±5-10% accuracy). Live pricing API not required."
- Cache stale + MCP available: "Pricing source: live AWS Price List API (via the
  AWS MCP server). Cache is stale ([date]) — using real-time pricing."
- Cache stale + MCP unavailable: "Pricing source: stale cache only (updated
  [date]). The AWS Price List API is unreachable. Proceeding with cached
  pricing; accuracy ±5-10% for infrastructure."
- Service not in cache + MCP unavailable: "Some services not in pricing cache
  and MCP unreachable. Those services will show `pricing_source: unavailable`
  in the estimate."

## Pricing hierarchy (per-service lookup order)

| Priority | Source                                               | Condition                                                                                      | `pricing_source` value |
| -------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------- |
| 1        | `references/vendored/pricing/aws-infra-pricing.json` | Service found in the pricing file                                                              | `"cached"`             |
| 2        | Price List API (`pricing.GetProducts`)               | Service NOT in the file, MCP available                                                         | `"live"`               |
| 3        | Pricing file after MCP failure                       | MCP attempted but failed, service IS in file                                                   | `"cached_fallback"`    |
| 4        | Formula constants / well-known published rate        | NOT in file, MCP failed, but the cost engine's own formulas carry the rate (state it verbatim) | `"estimated"`          |
| 5        | Unavailable                                          | NOT in file, MCP failed, no formula constant either                                            | `"unavailable"`        |

Row 4 is the documented home of the `services_by_source.estimated` bucket the
shared schema and assemblers carry: a service priced from a rate the cost
engine itself states (never a guessed or remembered number) is `"estimated"`,
always accompanied by a warning naming the rate and its source. Only a service
with no cache entry, no MCP, AND no stated formula rate is `"unavailable"` and
excluded from totals.
