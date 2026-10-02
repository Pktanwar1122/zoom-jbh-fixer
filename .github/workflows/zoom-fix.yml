name: Zoom join-before-host fixer
on:
  schedule:
    - cron: "*/5 * * * *"    # every 5 min (GitHub minimum; runs may start a few min late)
    - cron: "0 0 1 * *"      # monthly keepalive (stops GitHub auto-disabling after 60 days)
  workflow_dispatch: {}       # "Run workflow" button for manual runs

permissions:
  contents: read

jobs:
  fix:
    if: github.event.schedule != '0 0 1 * *'
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

  keepalive:
    if: github.event.schedule == '0 0 1 * *'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - run: |
          git config user.name "keepalive-bot"
          git config user.email "keepalive-bot@users.noreply.github.com"
          git commit --allow-empty -m "keepalive"
          git push
