# Reserved Instances

## What Are Reserved Instances?

Reserved instances are a billing commitment that provides a discount of 30–50%
in exchange for agreeing to use a specific instance type in a specific region
for 1 or 3 years.

## Commitment Types

| Term | Payment | Discount |
|------|---------|----------|
| 1 year | Monthly | 30% |
| 1 year | Full upfront | 35% |
| 3 years | Monthly | 45% |
| 3 years | Full upfront | 50% |

## Purchasing a Reservation

1. Navigate to **Settings → Billing → Reserved Instances → + Purchase**.
2. Select the instance type, region, term, and payment option.
3. Confirm. The reservation applies immediately to any matching running VM.

## How Reservations Are Applied

Reservations are applied automatically — no configuration required on the VM.
If you have a reservation for `standard-4` in `us-east-1` and you run a matching
VM, you are billed at the reserved rate for those hours.

## Unused Reservations

If you stop a VM covered by a reservation, you continue to be charged (the
reservation is for capacity, not usage). To avoid waste, keep reserved VMs
running or sell unused capacity (see Reservation Marketplace).

## Reservation Marketplace (Business & Enterprise)

Sell unused reservations to other Nirvana customers at a negotiated price:
**Settings → Billing → Reserved Instances → List for Sale**.

## Recommendations

Use **Settings → Billing → Cost Explorer → Reservation Recommendations** to see
which running on-demand VMs would benefit most from a reservation based on
your usage history.

## Scope

- **Regional**: Applies to any VM of the matching type in the specified region.
- **Zonal**: Applies to a specific availability zone, guarantees capacity (Enterprise).
