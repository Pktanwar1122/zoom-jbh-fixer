name: Zoom join-before-host fixer
on:
  schedule:
    - cron: "*/5 * * * *"    # every 5 min (GitHub minimum; runs may start a few min late)
  workflow_dispatch: {}       # "Run workflow" button for manual runs
 
permissions:
  contents: read
  actions: write              # lets keepalive stop GitHub auto-disabling this after 60 days
 
jobs:
  fix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install requests
      - run: python fix_zoom_jbh.py
        env:
          ZOOM_ACCOUNT_ID: ${{ secrets.ZOOM_ACCOUNT_ID }}
          ZOOM_CLIENT_ID: ${{ secrets.ZOOM_CLIENT_ID }}
          ZOOM_CLIENT_SECRET: ${{ secrets.ZOOM_CLIENT_SECRET }}
          ZOOM_USER_EMAIL: ${{ secrets.ZOOM_USER_EMAIL }}
          MATCH_TOPIC: ${{ vars.MATCH_TOPIC }}
          DRY_RUN: ${{ vars.DRY_RUN }}        # set "true" for first test run
          LOOKAHEAD_HOURS: "24"
      - uses: gautamkrishnar/keepalive-workflow@v2
 
