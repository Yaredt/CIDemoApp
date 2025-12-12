"""
Storage layer for leads using Azure Cosmos DB
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey

from agents.models import Lead
from config.settings import get_settings

logger = logging.getLogger(__name__)


class LeadStorage:
    """
    Storage layer for managing leads in Azure Cosmos DB.
    """

    def __init__(self):
        """Initialize storage connection"""
        self.settings = get_settings()
        self.client = None
        self.database = None
        self.container = None

    async def initialize(self) -> None:
        """Initialize Cosmos DB connection"""
        if self.client is None:
            self.client = CosmosClient(
                self.settings.cosmos_endpoint,
                credential=self.settings.cosmos_key
            )

            # Create database if not exists
            self.database = await self.client.create_database_if_not_exists(
                id=self.settings.cosmos_database
            )

            # Create container if not exists
            self.container = await self.database.create_container_if_not_exists(
                id=self.settings.cosmos_container,
                partition_key=PartitionKey(path="/company/industry"),
                offer_throughput=400
            )

            logger.info("Cosmos DB connection initialized")

    async def close(self) -> None:
        """Close Cosmos DB connection"""
        if self.client:
            await self.client.close()
            logger.info("Cosmos DB connection closed")

    async def store_lead(self, lead: Lead) -> None:
        """
        Store a single lead.

        Args:
            lead: Lead to store
        """
        await self.initialize()

        try:
            # Convert lead to dict
            lead_dict = lead.model_dump(mode="json")
            lead_dict["id"] = lead.id

            # Upsert (create or update)
            await self.container.upsert_item(lead_dict)

            logger.debug(f"Stored lead: {lead.id}")

        except Exception as e:
            logger.error(f"Failed to store lead {lead.id}: {e}")
            raise

    async def store_leads(self, leads: List[Lead]) -> None:
        """
        Store multiple leads.

        Args:
            leads: Leads to store
        """
        await self.initialize()

        # Store leads concurrently
        tasks = [self.store_lead(lead) for lead in leads]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Stored {len(leads)} leads")

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """
        Get a lead by ID.

        Args:
            lead_id: Lead ID

        Returns:
            Lead or None
        """
        await self.initialize()

        try:
            # Query for the lead
            query = f"SELECT * FROM c WHERE c.id = @lead_id"
            parameters = [{"name": "@lead_id", "value": lead_id}]

            items = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                items.append(item)

            if items:
                return Lead(**items[0])

            return None

        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {e}")
            return None

    async def get_top_leads(self, limit: int = 10) -> List[Lead]:
        """
        Get top ranked leads.

        Args:
            limit: Number of leads to return

        Returns:
            List of top leads
        """
        await self.initialize()

        try:
            query = """
                SELECT * FROM c
                WHERE c.score != null
                ORDER BY c.score.overall_score DESC
                OFFSET 0 LIMIT @limit
            """
            parameters = [{"name": "@limit", "value": limit}]

            leads = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                leads.append(Lead(**item))

            logger.info(f"Retrieved {len(leads)} top leads")
            return leads

        except Exception as e:
            logger.error(f"Failed to get top leads: {e}")
            return []

    async def get_leads_by_industry(self, industry: str) -> List[Lead]:
        """
        Get leads by industry.

        Args:
            industry: Industry name

        Returns:
            List of leads
        """
        await self.initialize()

        try:
            query = "SELECT * FROM c WHERE c.company.industry = @industry"
            parameters = [{"name": "@industry", "value": industry}]

            leads = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters
            ):
                leads.append(Lead(**item))

            return leads

        except Exception as e:
            logger.error(f"Failed to get leads for industry {industry}: {e}")
            return []

    async def export_leads(
        self,
        leads: List[Lead],
        format: str = "json",
        output_path: Optional[str] = None
    ) -> str:
        """
        Export leads to file.

        Args:
            leads: Leads to export
            format: Export format (json, csv)
            output_path: Output file path

        Returns:
            Path to exported file
        """
        if not output_path:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/leads_export_{timestamp}.{format}"

        if format == "json":
            return await self._export_json(leads, output_path)
        elif format == "csv":
            return await self._export_csv(leads, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def _export_json(self, leads: List[Lead], output_path: str) -> str:
        """Export to JSON"""
        with open(output_path, "w") as f:
            data = [lead.model_dump(mode="json") for lead in leads]
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported {len(leads)} leads to {output_path}")
        return output_path

    async def _export_csv(self, leads: List[Lead], output_path: str) -> str:
        """Export to CSV"""
        import csv

        with open(output_path, "w", newline="") as f:
            if not leads:
                return output_path

            # Define CSV columns
            fieldnames = [
                "id",
                "company_name",
                "industry",
                "website",
                "location",
                "employee_count",
                "overall_score",
                "fit_score",
                "intent_score",
                "timing_score",
                "buying_signals",
                "status",
                "created_at"
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for lead in leads:
                writer.writerow({
                    "id": lead.id,
                    "company_name": lead.company.name,
                    "industry": lead.company.industry.value,
                    "website": str(lead.company.website) if lead.company.website else "",
                    "location": lead.company.location or "",
                    "employee_count": lead.company.employee_count or "",
                    "overall_score": lead.score.overall_score if lead.score else 0,
                    "fit_score": lead.score.fit_score if lead.score else 0,
                    "intent_score": lead.score.intent_score if lead.score else 0,
                    "timing_score": lead.score.timing_score if lead.score else 0,
                    "buying_signals": ",".join([s.value for s in lead.buying_signals]),
                    "status": lead.status.value,
                    "created_at": lead.created_at.isoformat()
                })

        logger.info(f"Exported {len(leads)} leads to {output_path}")
        return output_path
