# Analytics

## Measurement Readiness

Current score: **74 / 100 — Usable with gaps**

| Category | Score | Notes |
| --- | ---: | --- |
| Decision Alignment | 18 / 25 | Tracks acquisition and lead intent, but business owners and dashboard consumers are not documented yet. |
| Event Model Clarity | 17 / 20 | Events use lowercase underscores and represent meaningful actions. |
| Data Accuracy & Integrity | 13 / 20 | App-level instrumentation exists; browser/provider validation still needs to be run after deploy. |
| Conversion Definition Quality | 12 / 15 | Lead-form success events are clear conversions. |
| Attribution & Context | 6 / 10 | Page path and provider auto-attribution are captured; UTM discipline needs a campaign guide. |
| Governance & Maintenance | 8 / 10 | This plan documents event ownership and naming expectations. |

## North Star

For the current public-site phase, use **qualified lead actions per week**:

- `newsletter_signup_completed`
- `contact_message_sent`

Once the agent runtime ships, replace this with a product usage metric such as weekly active organizations or completed trusted workflows.

## Tracking Plan

| Event | Description | Properties | Trigger | Decision Supported |
| --- | --- | --- | --- | --- |
| `page_viewed` | A route was viewed. | `page_path`, `page_search`, `page_title` | Route change | Which pages attract and retain attention. |
| `cta_clicked` | A meaningful CTA was clicked. | `label`, `section`, `placement`, `destination`, `variant` | Click on annotated CTA | Which calls to action drive intent. |
| `form_started` | A tracked form received first focus in the session. | `form_name`, `page_path` | First field focus | Where form intent starts. |
| `newsletter_signup_completed` | Newsletter / early-access signup succeeded. | `form_name`, `page_path` | Server action returned success | Acquisition conversion volume. |
| `newsletter_signup_failed` | Newsletter / early-access signup failed validation or submission. | `form_name`, `page_path` | Server action returned error | Form friction and reliability. |
| `contact_message_sent` | Contact request succeeded. | `form_name`, `page_path` | Server action returned success | High-intent lead volume. |
| `contact_message_failed` | Contact request failed validation or submission. | `form_name`, `page_path` | Server action returned error | Contact-form friction and reliability. |

## Conversions

| Conversion | Event | Counting | Used By |
| --- | --- | --- | --- |
| Early access signup | `newsletter_signup_completed` | Every successful submission; duplicate emails may be accepted as a UX success but deduped in the database. | Marketing, growth |
| Contact request | `contact_message_sent` | Every successful submission. | Sales, partnerships |

## Provider Setup

The app can send events to either GA4, PostHog, both, or neither.

Set these in `web/.env.local` or the deployment environment:

```env
NEXT_PUBLIC_GA_MEASUREMENT_ID="G-..."
NEXT_PUBLIC_POSTHOG_KEY="phc_..."
NEXT_PUBLIC_POSTHOG_HOST="https://app.posthog.com"
```

When no provider keys are configured, events still push to `window.dataLayer` for local debugging or a future GTM setup.

## Validation Checklist

- Confirm `page_viewed` fires once per route change.
- Confirm `cta_clicked` fires for hero, navbar, pricing, and CTA-band actions.
- Confirm lead-form events do not include email, name, company, or message text.
- Confirm no duplicate conversion fires after a single successful submission.
- Validate desktop and mobile navigation clicks.
- Validate provider real-time dashboards after deployment.
