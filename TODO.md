# Task: Append new df_api users to report-mikhmon-all (11).csv

## Steps:
- [x] Analyze files (CSV, routerOS.py, main.py, routes.py)
- [x] Create plan and get confirmation
- [ ] Add POST /append-new-users endpoint in route/routes.py:
  - Fetch df_api via get_all_users() + parsing
  - Load CSV, get existing usernames
  - Filter new users, assign next №
  - Append and save CSV (preserve summary)
- [ ] Test endpoint
- [ ] Update totals if needed

Current: Ready to implement endpoint.
