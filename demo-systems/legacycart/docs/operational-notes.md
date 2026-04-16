# Operational Notes

- Production deploys run through Jenkins using a shared service account.
- The nightly reconcile job SSHs into the application VM before querying PostgreSQL.
- There is no centralized metrics stack. Operators rely on log scraping and manual checks.
- Restore testing is inconsistent and RPO/RTO are not formally tracked.

