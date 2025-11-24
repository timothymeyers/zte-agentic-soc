#!/usr/bin/env python3
"""
Azure AI Search Setup Utility

This script initializes Azure AI Search indexes and loads data from the Attack dataset
for threat intelligence enrichment and MITRE ATT&CK context.

Usage:
    python utils/setup_ai_search.py --endpoint <endpoint_url> --key <api_key>

Environment Variables:
    AZURE_SEARCH_ENDPOINT: Azure AI Search service endpoint
    AZURE_SEARCH_API_KEY: Azure AI Search admin API key (or use Managed Identity)

Indexes Created:
    - attack-scenarios: Attack dataset scenarios with MITRE mappings
    - historical-incidents: GUIDE dataset incidents for RAG
    - threat-intelligence: IOC enrichment data (IP, domain, hash reputation)
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)

from src.data.datasets import AttackDatasetLoader
from src.shared.logging import get_logger

logger = get_logger(__name__)


class AISearchSetup:
    """Azure AI Search initialization and data loading"""

    def __init__(self, endpoint: str, credential):
        self.endpoint = endpoint
        self.credential = credential
        self.index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

    async def create_attack_scenarios_index(self) -> None:
        """Create index for Attack dataset scenarios with MITRE mappings"""
        logger.info("Creating attack-scenarios index...")

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(
                name="name",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
            ),
            SearchableField(
                name="description",
                type=SearchFieldDataType.String,
                searchable=True,
            ),
            SearchableField(
                name="mitre_techniques",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True,
            ),
            SearchableField(
                name="mitre_tactics",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True,
            ),
            SimpleField(
                name="severity",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SearchableField(
                name="iocs",
                type=SearchFieldDataType.String,
                searchable=True,
            ),
            SearchableField(
                name="attack_scenario",
                type=SearchFieldDataType.String,
                searchable=True,
            ),
        ]

        index = SearchIndex(name="attack-scenarios", fields=fields)

        try:
            await self.index_client.create_or_update_index(index)
            logger.info("✅ attack-scenarios index created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create attack-scenarios index: {e}")
            raise

    async def create_historical_incidents_index(self) -> None:
        """Create index for GUIDE dataset historical incidents (RAG)"""
        logger.info("Creating historical-incidents index...")

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
            ),
            SearchableField(
                name="description",
                type=SearchFieldDataType.String,
                searchable=True,
            ),
            SimpleField(
                name="severity",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SimpleField(
                name="status",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SearchableField(
                name="entities",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True,
            ),
            SimpleField(
                name="resolution",
                type=SearchFieldDataType.String,
            ),
        ]

        index = SearchIndex(name="historical-incidents", fields=fields)

        try:
            await self.index_client.create_or_update_index(index)
            logger.info("✅ historical-incidents index created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create historical-incidents index: {e}")
            raise

    async def create_threat_intelligence_index(self) -> None:
        """Create index for threat intelligence IOC data"""
        logger.info("Creating threat-intelligence index...")

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(
                name="ioc_type",
                type=SearchFieldDataType.String,
                filterable=True,
            ),  # ip, domain, hash
            SearchableField(
                name="ioc_value",
                type=SearchFieldDataType.String,
                searchable=True,
            ),
            SimpleField(
                name="reputation_score",
                type=SearchFieldDataType.Int32,
                filterable=True,
            ),  # 0-100
            SearchableField(
                name="threat_actor",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
            ),
            SearchableField(
                name="campaigns",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
            ),
            SearchableField(
                name="mitre_techniques",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True,
            ),
        ]

        index = SearchIndex(name="threat-intelligence", fields=fields)

        try:
            await self.index_client.create_or_update_index(index)
            logger.info("✅ threat-intelligence index created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create threat-intelligence index: {e}")
            raise

    async def load_attack_data(self) -> None:
        """Load Attack dataset into attack-scenarios index"""
        logger.info("Loading Attack dataset into attack-scenarios index...")

        try:
            # Load Attack dataset
            loader = AttackDatasetLoader()
            scenarios = loader.load_scenarios()
            
            if not scenarios:
                logger.warning("No scenarios loaded from Attack dataset")
                return
            
            # Transform to search documents
            documents = []
            for scenario in scenarios:
                doc = {
                    "id": scenario["scenario_id"],
                    "name": scenario["name"],
                    "description": scenario["description"],
                    "mitre_techniques": [scenario["technique"]],
                    "mitre_tactics": [scenario["tactic"]],
                    "severity": scenario["severity"],
                    "iocs": ", ".join(scenario.get("indicators", [])),
                    "attack_scenario": scenario["description"]
                }
                documents.append(doc)
            
            # Batch upload to AI Search
            search_client = SearchClient(
                endpoint=self.endpoint,
                index_name="attack-scenarios",
                credential=self.credential
            )
            
            async with search_client:
                result = await search_client.upload_documents(documents=documents)
                logger.info(f"✅ Uploaded {len(documents)} attack scenarios to AI Search")
                
                # Check for any failures
                failed = [r for r in result if not r.succeeded]
                if failed:
                    logger.warning(f"⚠️  {len(failed)} documents failed to upload")
                
        except Exception as e:
            logger.error(f"❌ Failed to load Attack dataset: {e}")
            raise

    async def setup_all(self) -> None:
        """Create all indexes and load data"""
        try:
            logger.info("Starting Azure AI Search setup...")

            # Create indexes
            await self.create_attack_scenarios_index()
            await self.create_historical_incidents_index()
            await self.create_threat_intelligence_index()

            # Load data
            await self.load_attack_data()

            logger.info("✅ Azure AI Search setup complete!")

        except Exception as e:
            logger.error(f"❌ Azure AI Search setup failed: {e}")
            raise
        finally:
            await self.index_client.close()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Setup Azure AI Search indexes")
    parser.add_argument(
        "--endpoint",
        help="Azure AI Search endpoint URL",
        default=os.getenv("AZURE_SEARCH_ENDPOINT"),
    )
    parser.add_argument(
        "--key",
        help="Azure AI Search API key (or use Managed Identity)",
        default=os.getenv("AZURE_SEARCH_API_KEY"),
    )
    parser.add_argument(
        "--use-managed-identity",
        action="store_true",
        help="Use Azure Managed Identity instead of API key",
    )

    args = parser.parse_args()

    if not args.endpoint:
        print(
            "❌ Error: Azure AI Search endpoint required (--endpoint or AZURE_SEARCH_ENDPOINT)"
        )
        sys.exit(1)

    # Setup credential
    if args.use_managed_identity or not args.key:
        logger.info("Using Azure Managed Identity for authentication")
        credential = DefaultAzureCredential()
    else:
        logger.info("Using API key for authentication")
        credential = AzureKeyCredential(args.key)

    # Run setup
    setup = AISearchSetup(endpoint=args.endpoint, credential=credential)
    await setup.setup_all()


if __name__ == "__main__":
    asyncio.run(main())
