# Prototype Feature Boundaries

Several capabilities in the historical AgricultureMonitoring archive
were prototypes rather than completed production features.

## Subscription tiers

The interface contains Standard, Researcher, and Premium concepts.

Historically, the upgrade endpoint directly changed the user's tier in
the database while checkout was mocked.

The maintained repository does not present this as payment integration.

Direct tier mutation through the upgrade endpoint is disabled.

## Custom Python execution

The historical ML interface included a browser editor that executed
arbitrary submitted Python code on the Django server.

That feature is removed.

It is not described as sandboxed execution because the historical
implementation did not provide a secure execution sandbox.

## Pretrained-model demonstration

The historical project contained a synthetic-data demonstration that
depended on a workstation-specific Excel file.

That feature remains disabled until its dataset and prediction semantics
can be represented reproducibly.

## Image AI overlay

The historical image workflow displayed demonstration AI labels without
executing a corresponding maintained inference model.

That overlay was removed during repository sanitization.

## Future work

These concepts may be implemented later as genuine features.

The maintained repository only claims capabilities supported by current
source code and reproducible evidence.
