#!/usr/bin/env python3
"""
Export all Dependabot alerts from a GitHub repository.
Requires: requests, pandas (optional for CSV export)

Usage:
    python export_dependabot_alerts.py --owner OWNER --repo REPO --token TOKEN

Environment variables:
    GITHUB_TOKEN: GitHub personal access token (alternative to --token)
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


class DependabotAlertsExporter:
    """Export Dependabot alerts from a GitHub repository."""

    def __init__(self, owner: str, repo: str, token: str):
        """
        Initialize the exporter.

        Args:
            owner: Repository owner
            repo: Repository name
            token: GitHub personal access token
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.alerts: List[Dict[str, Any]] = []

    def fetch_alerts(self, state: str = "open", per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch all Dependabot alerts from the repository.

        Args:
            state: Alert state ('open', 'dismissed', 'resolved')
            per_page: Results per page (max 100)

        Returns:
            List of alert dictionaries
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/dependabot/alerts"
        params = {
            "state": state,
            "per_page": per_page,
            "sort": "updated",
            "direction": "desc",
        }

        page = 1
        alerts = []

        print(f"Fetching {state} Dependabot alerts...")

        while True:
            params["page"] = page
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 404:
                print(
                    "Error: Could not find repository or alerts endpoint is not available."
                )
                print(
                    "Make sure: 1) Token has 'repo' scope, 2) Repository exists, 3) You have access"
                )
                sys.exit(1)

            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                sys.exit(1)

            page_alerts = response.json()

            if not page_alerts:
                break

            alerts.extend(page_alerts)
            print(f"  Fetched page {page}: {len(page_alerts)} alerts (total: {len(alerts)})")

            page += 1

        self.alerts = alerts
        return alerts

    def export_json(self, filename: str = None) -> str:
        """
        Export alerts to JSON file.

        Args:
            filename: Output filename (default: dependabot_alerts_TIMESTAMP.json)

        Returns:
            Path to created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dependabot_alerts_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(self.alerts, f, indent=2, default=str)

        print(f"\n✓ Exported {len(self.alerts)} alerts to {filename}")
        return filename

    def export_csv(self, filename: str = None) -> str:
        """
        Export alerts to CSV file.

        Args:
            filename: Output filename (default: dependabot_alerts_TIMESTAMP.csv)

        Returns:
            Path to created file
        """
        try:
            import pandas as pd
        except ImportError:
            print("Error: pandas library not found. Install with: pip install pandas")
            sys.exit(1)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dependabot_alerts_{timestamp}.csv"

        # Flatten nested data
        rows = []
        for alert in self.alerts:
            row = {
                "number": alert.get("number"),
                "state": alert.get("state"),
                "dependency": alert.get("dependency", {}).get("package", {}).get("name"),
                "ecosystem": alert.get("dependency", {}).get("package", {}).get("ecosystem"),
                "vulnerability_severity": alert.get("security_advisory", {}).get("severity"),
                "vulnerability_cve": alert.get("security_advisory", {}).get("cve_id"),
                "updated_at": alert.get("updated_at"),
                "created_at": alert.get("created_at"),
                "dismissed_at": alert.get("dismissed_at"),
                "url": alert.get("html_url"),
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)

        print(f"\n✓ Exported {len(self.alerts)} alerts to {filename}")
        return filename

    def export_markdown(self, filename: str = None) -> str:
        """
        Export alerts to Markdown file.

        Args:
            filename: Output filename (default: DEPENDABOT_ALERTS.md)

        Returns:
            Path to created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dependabot_alerts_{timestamp}.md"

        with open(filename, "w") as f:
            f.write("# Dependabot Alerts\n\n")
            f.write(
                f"Repository: `{self.owner}/{self.repo}`\n"
            )
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Alerts: {len(self.alerts)}\n\n")

            # Summary by severity
            severity_counts = {}
            for alert in self.alerts:
                severity = alert.get("security_advisory", {}).get("severity", "unknown")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            f.write("## Summary by Severity\n\n")
            for severity, count in sorted(severity_counts.items(), reverse=True):
                f.write(f"- **{severity.upper()}**: {count}\n")

            f.write("\n## Alerts\n\n")

            for alert in self.alerts:
                package = alert.get("dependency", {}).get("package", {}).get("name", "Unknown")
                severity = alert.get("security_advisory", {}).get("severity", "unknown")
                cve = alert.get("security_advisory", {}).get("cve_id", "N/A")
                state = alert.get("state", "unknown")
                url = alert.get("html_url", "#")

                f.write(f"### #{alert.get('number', 'N/A')} - {package}\n\n")
                f.write(f"**Status**: {state}\n\n")
                f.write(f"**Severity**: {severity}\n\n")
                f.write(f"**CVE**: {cve}\n\n")
                f.write(f"**URL**: [{url}]({url})\n\n")
                f.write("---\n\n")

        print(f"\n✓ Exported {len(self.alerts)} alerts to {filename}")
        return filename

    def print_summary(self):
        """Print a summary of the alerts."""
        print("\n" + "=" * 60)
        print("DEPENDABOT ALERTS SUMMARY")
        print("=" * 60)
        print(f"Repository: {self.owner}/{self.repo}")
        print(f"Total Alerts: {len(self.alerts)}")

        # Group by severity
        severity_counts = {}
        for alert in self.alerts:
            severity = alert.get("security_advisory", {}).get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        print("\nBy Severity:")
        for severity in ["critical", "high", "medium", "low", "unknown"]:
            if severity in severity_counts:
                print(f"  {severity.upper()}: {severity_counts[severity]}")

        # Group by ecosystem
        ecosystem_counts = {}
        for alert in self.alerts:
            ecosystem = alert.get("dependency", {}).get("package", {}).get("ecosystem", "unknown")
            ecosystem_counts[ecosystem] = ecosystem_counts.get(ecosystem, 0) + 1

        print("\nBy Ecosystem:")
        for ecosystem, count in sorted(ecosystem_counts.items()):
            print(f"  {ecosystem}: {count}")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Export Dependabot alerts from a GitHub repository"
    )
    parser.add_argument("--owner", required=True, help="Repository owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub personal access token (or use GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--state",
        default="open",
        choices=["open", "dismissed", "resolved"],
        help="Alert state to fetch (default: open)",
    )
    parser.add_argument(
        "--format",
        default="json",
        choices=["json", "csv", "markdown", "all"],
        help="Export format (default: json)",
    )
    parser.add_argument(
        "--output",
        help="Output filename (default: auto-generated based on timestamp)",
    )

    args = parser.parse_args()

    if not args.token:
        print("Error: GitHub token not provided. Set GITHUB_TOKEN env var or use --token")
        sys.exit(1)

    exporter = DependabotAlertsExporter(args.owner, args.repo, args.token)

    # Fetch alerts
    alerts = exporter.fetch_alerts(state=args.state)

    if not alerts:
        print(f"No {args.state} alerts found.")
        return

    # Print summary
    exporter.print_summary()

    # Export
    if args.format == "json":
        exporter.export_json(args.output)
    elif args.format == "csv":
        exporter.export_csv(args.output)
    elif args.format == "markdown":
        exporter.export_markdown(args.output)
    elif args.format == "all":
        exporter.export_json(args.output.replace(".json", "") if args.output else None)
        exporter.export_csv(args.output.replace(".csv", "") if args.output else None)
        exporter.export_markdown(
            args.output.replace(".md", "") if args.output else None
        )


if __name__ == "__main__":
    main()
