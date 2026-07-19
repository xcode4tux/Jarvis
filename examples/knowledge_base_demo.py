"""
Knowledge Base Demo — Cerebras-style RAG System

This demo shows how to build a company knowledge base similar to the one
described by Cerebras, using OpenJarvis's existing infrastructure.

The system implements:
1. Multi-source data ingestion (Slack, Gmail, GitHub, etc.)
2. Semantic chunking with metadata enrichment
3. Two-stage retrieval (BM25 + ColBERT reranking)
4. Source-aware filtering (by date, author, channel, etc.)

Usage:
    python examples/knowledge_base_demo.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from openjarvis.connectors._stubs import Document
from openjarvis.connectors.embedding_store import EmbeddingStore
from openjarvis.connectors.embeddings import OllamaEmbedder
from openjarvis.connectors.pipeline import IngestionPipeline
from openjarvis.connectors.retriever import ColBERTReranker, TwoStageRetriever
from openjarvis.connectors.store import KnowledgeStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_basic_knowledge_base():
    """Demonstrate basic knowledge base creation and querying."""
    
    print("=" * 80)
    print("DEMO: Building a Cerebras-style Knowledge Base")
    print("=" * 80)
    
    # Step 1: Create the knowledge store (SQLite + FTS5)
    print("\n[1/5] Creating knowledge store...")
    db_path = Path("/tmp/demo_knowledge.db")
    if db_path.exists():
        db_path.unlink()
    
    store = KnowledgeStore(db_path=str(db_path))
    print(f"✓ Created knowledge store at {db_path}")
    
    # Step 2: Set up embedding model (optional but recommended for semantic search)
    print("\n[2/5] Setting up embedder...")
    try:
        embedder = OllamaEmbedder(model="nomic-embed-text")
        print(f"✓ Using embedding model: {embedder.model_version}")
    except Exception as e:
        logger.warning(f"Embedder not available ({e}), continuing without embeddings")
        embedder = None
    
    # Step 3: Create ingestion pipeline
    print("\n[3/5] Creating ingestion pipeline...")
    pipeline = IngestionPipeline(
        store=store,
        max_tokens=512,
        embedder=embedder,
    )
    print("✓ Ingestion pipeline ready")
    
    # Step 4: Simulate data from multiple sources (like Slack, Gmail, GitHub)
    print("\n[4/5] Ingesting sample documents...")
    
    # Simulate Slack messages
    slack_docs = [
        Document(
            doc_id="slack:C123ABC:1710500000.000100",
            content="""
[Thread: #engineering-support]
Amaya (9:14 AM): Hey, the restore gets stuck in the larger cluster after manifest 
loading, but small runs are okay. I can reproduce this with 128 GPUs. The protocol 
stops before the cache warms up.

Nick (9:32 AM): This looks like the issue we saw last month. Try increasing the 
cache_warmup_timeout in the config to 300s. Also check if the nodes have enough 
memory pressure during the restore phase.

Amaya (9:45 AM): That worked! The restore completed successfully. Should we update 
the runbook with this?

Nick (10:02 AM): Yes, please create a PR to add this to the troubleshooting guide.
""",
            source="slack",
            source_id="C123ABC:1710500000.000100",
            doc_type="conversation",
            title="#engineering-support: Restore issue discussion",
            author="Amaya",
            participants=["Amaya", "Nick"],
            timestamp=datetime(2024, 3, 15, 9, 14),
            thread_id="slack:C123ABC:thread_001",
            channel="engineering-support",
            metadata={
                "workspace": "acme",
                "resolution": "Increased cache_warmup_timeout to 300s",
            },
        ),
        Document(
            doc_id="slack:C456DEF:1710586400.000200",
            content="""
[Thread: #general]
Sarah (2:00 PM): Quick reminder that we're switching to the new deployment pipeline 
next week. All teams should have received the migration guide.

Mike (2:15 PM): Does this affect the staging environment too or just production?

Sarah (2:30 PM): Both environments will be migrated. The staging migration happens 
on Tuesday, production on Thursday. Please test your services in staging first.
""",
            source="slack",
            source_id="C456DEF:1710586400.000200",
            doc_type="conversation",
            title="#general: Deployment pipeline migration",
            author="Sarah",
            participants=["Sarah", "Mike"],
            timestamp=datetime(2024, 3, 16, 14, 0),
            thread_id="slack:C456DEF:thread_002",
            channel="general",
            metadata={"workspace": "acme"},
        ),
    ]
    
    # Simulate Gmail messages
    gmail_docs = [
        Document(
            doc_id="gmail:18e4f2a3b5c6d7e8",
            content="""
From: Alex Chen <alex@partner-company.com>
To: Nick Zaroff <nick@nixaroffmedia.com>
Subject: Re: Q2 AI Infrastructure Partnership Proposal

Hi Nick,

Thanks for the detailed proposal. We're very interested in partnering for Q2. 
Our team has reviewed the technical specifications and we believe the Cerebras 
inference chips would significantly accelerate our model training pipeline.

Key points from our review:
1. Performance benchmarks look impressive (5x speedup vs current setup)
2. Power efficiency aligns with our sustainability goals
3. Integration timeline is feasible for our Q2 roadmap

Next steps:
- Schedule technical deep-dive with engineering team (week of March 25)
- Finalize pricing and SLA terms
- Draft partnership agreement

Looking forward to moving this forward.

Best regards,
Alex Chen
VP of Engineering, Partner Company
""",
            source="gmail",
            source_id="18e4f2a3b5c6d7e8",
            doc_type="email",
            title="Re: Q2 AI Infrastructure Partnership Proposal",
            author="Alex Chen",
            participants=["Alex Chen", "Nick Zaroff"],
            timestamp=datetime(2024, 3, 18, 11, 30),
            metadata={
                "labels": ["important", "partnership"],
                "has_attachment": False,
            },
        ),
    ]
    
    # Simulate GitHub activity
    github_docs = [
        Document(
            doc_id="github:open-jarvis/OpenJarvis:PR-123",
            content="""
Pull Request #123: Add troubleshooting guide for restore timeouts

Author: Amaya <amaya@company.com>
Labels: documentation, bugfix
Status: Merged

Description:
This PR adds a new section to the troubleshooting guide covering the restore 
timeout issue that occurred on March 15th. The root cause was insufficient 
cache_warmup_timeout configuration for large cluster restores (>100 GPUs).

Changes:
- Added 'Restore Timeouts' section to docs/troubleshooting.md
- Included step-by-step diagnosis procedure
- Added recommended timeout values based on cluster size
- Linked to relevant Slack thread for context

Fixes issue #118
""",
            source="github",
            source_id="open-jarvis/OpenJarvis:PR-123",
            doc_type="pull_request",
            title="Add troubleshooting guide for restore timeouts",
            author="Amaya",
            participants=["Amaya"],
            timestamp=datetime(2024, 3, 15, 15, 30),
            metadata={
                "repository": "open-jarvis/OpenJarvis",
                "pr_number": 123,
                "status": "merged",
                "labels": ["documentation", "bugfix"],
            },
        ),
    ]
    
    # Simulate internal wiki/SOP document
    wiki_docs = [
        Document(
            doc_id="wiki:onboarding:ai-infrastructure",
            content="""
# AI Infrastructure Onboarding Guide

Welcome to the team! This guide will help you get up to speed with our AI 
infrastructure stack.

## Overview

We use Cerebras inference chips for large-scale model training and inference. 
Our current setup includes:
- 4 CS-2 clusters (each with 400k cores)
- Distributed training across multiple data centers
- Custom caching layer for model weights

## Common Issues & Solutions

### Restore Timeouts

**Problem**: Large cluster restores (>100 GPUs) fail during manifest loading.

**Symptoms**:
- Restore process hangs after "Loading manifest..." message
- Small runs (<50 GPUs) work fine
- Error appears 2-3 minutes into restore

**Solution**:
1. Increase `cache_warmup_timeout` in config.yaml to 300s
2. Monitor memory pressure during restore: `watch -n 1 free -h`
3. If still failing, reduce batch size temporarily

**Root Cause**: Default timeout (60s) is insufficient for warming up cache 
across all nodes in large clusters.

### Cache Misses

**Problem**: High latency during inference due to cache misses.

**Solution**: Pre-warm cache with common queries before peak hours.

## Contact

For infrastructure questions, reach out to #engineering-support or page 
the on-call engineer.
""",
            source="wiki",
            source_id="onboarding:ai-infrastructure",
            doc_type="documentation",
            title="AI Infrastructure Onboarding Guide",
            author="Engineering Team",
            timestamp=datetime(2024, 3, 1, 10, 0),
            metadata={
                "category": "onboarding",
                "tags": ["infrastructure", "cerebras", "troubleshooting"],
                "last_updated": "2024-03-15",
            },
        ),
    ]
    
    # Combine all documents
    all_docs = slack_docs + gmail_docs + github_docs + wiki_docs
    
    # Ingest documents
    chunks_stored = pipeline.ingest(all_docs)
    print(f"✓ Ingested {len(all_docs)} documents → {chunks_stored} chunks")
    
    # Step 5: Set up retriever with two-stage retrieval
    print("\n[5/5] Setting up two-stage retriever...")
    
    # Optional: Set up ColBERT reranker for semantic re-ranking
    try:
        reranker = ColBERTReranker(
            checkpoint="colbert-ir/colbertv2.0",
            embedding_store=EmbeddingStore(db_path="/tmp/colbert_cache.db"),
        )
        print("✓ ColBERT reranker initialized")
    except Exception as e:
        logger.warning(f"ColBERT not available ({e}), using BM25 only")
        reranker = None
    
    retriever = TwoStageRetriever(
        store=store,
        reranker=reranker,
        recall_k=100,
    )
    print("✓ Two-stage retriever ready")
    
    # Demonstrate queries
    print("\n" + "=" * 80)
    print("QUERY DEMONSTRATIONS")
    print("=" * 80)
    
    # Query 1: Technical troubleshooting question
    print("\n[Query 1] 'Why does the restore hang after loading manifest?'")
    print("-" * 80)
    results = retriever.retrieve(
        "restore hang manifest loading timeout",
        top_k=3,
    )
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f} | Source: {result.source}")
        print(f"   Title: {result.metadata.get('title', 'N/A')}")
        print(f"   Author: {result.metadata.get('author', 'N/A')}")
        print(f"   Date: {result.metadata.get('timestamp', 'N/A')[:10]}")
        print(f"   Content: {result.content[:200]}...")
    
    # Query 2: Find recent discussions by specific person
    print("\n\n[Query 2] 'What did Nick talk about recently?'")
    print("-" * 80)
    results = retriever.retrieve(
        "Nick discussion conversation",
        top_k=3,
        author="Nick",
    )
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f} | Source: {result.source}")
        print(f"   Channel: {result.metadata.get('channel', 'N/A')}")
        print(f"   Date: {result.metadata.get('timestamp', 'N/A')[:10]}")
        print(f"   Content: {result.content[:200]}...")
    
    # Query 3: Filter by date range (recent only)
    print("\n\n[Query 3] 'Deployment pipeline changes' (last 7 days)")
    print("-" * 80)
    since_date = (datetime.now() - timedelta(days=7)).isoformat()
    results = retriever.retrieve(
        "deployment pipeline migration",
        top_k=3,
        since=since_date,
    )
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f} | Source: {result.source}")
        print(f"   Date: {result.metadata.get('timestamp', 'N/A')[:10]}")
        print(f"   Content: {result.content[:200]}...")
    
    # Query 4: Filter by source (only GitHub)
    print("\n\n[Query 4] 'Recent pull requests' (GitHub only)")
    print("-" * 80)
    results = retriever.retrieve(
        "pull request merged",
        top_k=3,
        source="github",
        doc_type="pull_request",
    )
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f}")
        print(f"   Repository: {result.metadata.get('repository', 'N/A')}")
        print(f"   PR #{result.metadata.get('pr_number', 'N/A')}")
        print(f"   Status: {result.metadata.get('status', 'N/A')}")
        print(f"   Content: {result.content[:200]}...")
    
    # Query 5: Cross-source synthesis
    print("\n\n[Query 5] 'Partnership proposals and sponsorships'")
    print("-" * 80)
    results = retriever.retrieve(
        "partnership proposal sponsorship deal",
        top_k=3,
    )
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f} | Source: {result.source}")
        print(f"   Type: {result.metadata.get('doc_type', 'N/A')}")
        print(f"   From: {result.metadata.get('author', 'N/A')}")
        print(f"   Content: {result.content[:200]}...")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("✓ Multi-source ingestion (Slack, Gmail, GitHub, Wiki)")
    print("✓ Rich metadata enrichment (timestamps, authors, participants, channels)")
    print("✓ Semantic chunking with configurable token limits")
    print("✓ Two-stage retrieval (BM25 + optional ColBERT reranking)")
    print("✓ Source-aware filtering (by source, doc_type, author, date range)")
    print("✓ Provenance tracking for every chunk")
    print("\nThis matches the Cerebras knowledge base architecture!")
    print("=" * 80)
    
    return store, retriever


if __name__ == "__main__":
    store, retriever = demo_basic_knowledge_base()
