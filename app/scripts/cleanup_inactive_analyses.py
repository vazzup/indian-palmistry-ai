#!/usr/bin/env python3
"""
Cleanup script for inactive analyses and their associated files.

This script can be run manually or via a cron job to clean up
analyses that have been marked as inactive for a specified period.

Usage:
    python -m app.scripts.cleanup_inactive_analyses [--days=7] [--dry-run]
"""

import asyncio
import argparse
import logging
import sys
from typing import Dict, Any
from app.services.cleanup_service import CleanupService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(description='Clean up inactive palm reading analyses')
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Delete analyses inactive for more than this many days (default: 7)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting anything'
    )
    parser.add_argument(
        '--force-analysis-id',
        type=int,
        help='Force cleanup of a specific analysis ID (ignores age check)'
    )

    args = parser.parse_args()

    cleanup_service = CleanupService()

    try:
        if args.force_analysis_id:
            logger.info(f"Force cleaning up analysis {args.force_analysis_id}")
            success = await cleanup_service.force_cleanup_analysis(args.force_analysis_id)
            if success:
                logger.info(f"Successfully cleaned up analysis {args.force_analysis_id}")
            else:
                logger.error(f"Failed to clean up analysis {args.force_analysis_id}")
                sys.exit(1)
            return

        if args.dry_run:
            logger.info(f"DRY RUN: Estimating cleanup impact for analyses inactive for >{args.days} days")
            stats = await cleanup_service.estimate_cleanup_impact(args.days)
            print_cleanup_estimate(stats)
        else:
            logger.info(f"Cleaning up analyses inactive for >{args.days} days")
            stats = await cleanup_service.cleanup_inactive_analyses(args.days)
            print_cleanup_results(stats)

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)


def print_cleanup_estimate(stats: Dict[str, Any]) -> None:
    """Print estimated cleanup impact."""
    print("\n" + "="*50)
    print("CLEANUP ESTIMATE")
    print("="*50)
    print(f"Analyses to be deleted: {stats['analyses_to_clean']}")
    print(f"Local files to be deleted: {stats['files_to_delete']}")
    print(f"OpenAI files to be deleted: {stats['openai_files_to_delete']}")

    if stats['analyses_to_clean'] > 0:
        print(f"Date range: {stats['oldest_analysis_date']} to {stats['newest_analysis_date']}")
        print("\nTo perform the actual cleanup, run without --dry-run flag")
    else:
        print("\nNo analyses need cleanup at this time.")

    print("="*50)


def print_cleanup_results(stats: Dict[str, Any]) -> None:
    """Print actual cleanup results."""
    print("\n" + "="*50)
    print("CLEANUP RESULTS")
    print("="*50)
    print(f"Analyses deleted: {stats['analyses_cleaned']}")
    print(f"Local files deleted: {stats['files_deleted']}")
    print(f"OpenAI files deleted: {stats['openai_files_deleted']}")

    if stats['errors']:
        print(f"\nErrors encountered ({len(stats['errors'])}):")
        for error in stats['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")
    else:
        print("\nNo errors encountered.")

    print("="*50)

    if stats['analyses_cleaned'] > 0:
        print("✅ Cleanup completed successfully!")
    else:
        print("ℹ️  No analyses were cleaned up (none met the criteria).")


if __name__ == "__main__":
    asyncio.run(main())