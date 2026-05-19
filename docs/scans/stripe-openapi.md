# Tool Tax Report

Grade: **brutal**

| Metric | Value |
| --- | ---: |
| Tools | 587 |
| Full tool tax | 649,797 est. tokens |
| Slim index | 28,047 est. tokens |
| Slim-index savings | 621,750 est. tokens (95.7%) |
| Worst tool | 18,712 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `PostPaymentIntents` | 18,712 | 53 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/payment_intents/post` |
| `PostPaymentIntentsIntentConfirm` | 17,504 | 48 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/payment_intents/{intent}/confirm/post` |
| `PostPaymentIntentsIntent` | 17,462 | 52 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/payment_intents/{intent}/post` |
| `PostCheckoutSessions` | 17,376 | 41 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/checkout/sessions/post` |
| `PostTaxRegistrations` | 11,054 | 49 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/tax/registrations/post` |
| `PostAccounts` | 10,747 | 62 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/accounts/post` |
| `PostPaymentMethodConfigurationsConfiguration` | 10,545 | 39 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/payment_method_configurations/{configuration}/post` |
| `PostPaymentMethodConfigurations` | 10,500 | 40 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/payment_method_configurations/post` |
| `PostAccountsAccount` | 10,069 | 60 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/accounts/{account}/post` |
| `PostSetupIntents` | 9,531 | 54 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/setup_intents/post` |
| `PostSetupIntentsIntent` | 8,575 | 40 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/setup_intents/{intent}/post` |
| `PostSubscriptionsSubscriptionExposedId` | 8,374 | 46 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/subscriptions/{subscription_exposed_id}/post` |
| `PostSetupIntentsIntentConfirm` | 8,310 | 49 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/setup_intents/{intent}/confirm/post` |
| `PostSubscriptions` | 7,654 | 49 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/subscriptions/post` |
| `PostInvoicesCreatePreview` | 7,627 | 48 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/invoices/create_preview/post` |
| `PostCustomersCustomerSubscriptionsSubscriptionExposedId` | 7,562 | 47 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/customers/{customer}/subscriptions/{subscription_exposed_id}/post` |
| `PostPaymentMethods` | 7,113 | 59 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/payment_methods/post` |
| `PostPaymentLinks` | 7,082 | 40 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/payment_links/post` |
| `PostCustomersCustomerSubscriptions` | 7,017 | 44 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/customers/{customer}/subscriptions/post` |
| `PostTokens` | 6,611 | 52 | `/tmp/tool-tax-public-scans/stripe-openapi.json/paths//v1/tokens/post` |

## What To Do

- Do not always-load full schemas. Generate a slim index and lazy-load schemas.
- Split or shorten the heaviest tool schema; one tool exceeds 750 estimated tokens.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
