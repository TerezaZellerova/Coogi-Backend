#!/usr/bin/env python3
"""
Cleanup script to remove duplicate progressive agents
"""
import asyncio
import os
import sys
import logging
from typing import Dict, List
from datetime import datetime

# Add the current directory to the path so we can import from utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.progressive_agent_manager import progressive_agent_manager
from utils.progressive_agent_db import progressive_agent_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_duplicate_agents():
    """Remove duplicate progressive agents, keeping only the most recent one for each query"""
    try:
        logger.info("🧹 Starting cleanup of duplicate progressive agents...")
        
        # Get all agents
        agents = progressive_agent_manager.get_all_agents()
        logger.info(f"Found {len(agents)} total agents")
        
        # Group agents by query
        agents_by_query: Dict[str, List] = {}
        for agent in agents:
            query = agent.query.strip().lower()
            if query not in agents_by_query:
                agents_by_query[query] = []
            agents_by_query[query].append(agent)
        
        # Find duplicates
        agents_to_remove = []
        agents_to_keep = []
        
        for query, agent_list in agents_by_query.items():
            if len(agent_list) > 1:
                logger.info(f"📋 Found {len(agent_list)} duplicates for query: '{query}'")
                
                # Sort by creation date (most recent first)
                agent_list.sort(key=lambda x: x.created_at, reverse=True)
                
                # Keep the most recent one
                most_recent = agent_list[0]
                agents_to_keep.append(most_recent)
                logger.info(f"✅ Keeping most recent agent: {most_recent.id} (created: {most_recent.created_at})")
                
                # Mark the rest for removal
                for old_agent in agent_list[1:]:
                    agents_to_remove.append(old_agent)
                    logger.info(f"❌ Marking for removal: {old_agent.id} (created: {old_agent.created_at})")
            else:
                # Only one agent for this query, keep it
                agents_to_keep.append(agent_list[0])
        
        logger.info(f"📊 Summary:")
        logger.info(f"   - Total agents: {len(agents)}")
        logger.info(f"   - Agents to keep: {len(agents_to_keep)}")
        logger.info(f"   - Agents to remove: {len(agents_to_remove)}")
        
        if agents_to_remove:
            # Remove duplicates from memory
            for agent in agents_to_remove:
                if agent.id in progressive_agent_manager.active_agents:
                    del progressive_agent_manager.active_agents[agent.id]
                    logger.info(f"🗑️ Removed from memory: {agent.id}")
            
            # Remove from database (if database cleanup is implemented)
            try:
                for agent in agents_to_remove:
                    await progressive_agent_db.delete_agent(agent.id)
                    logger.info(f"🗑️ Removed from database: {agent.id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not clean database (method may not exist): {e}")
            
            logger.info(f"✅ Cleanup completed! Removed {len(agents_to_remove)} duplicate agents")
        else:
            logger.info("✨ No duplicates found - database is clean!")
            
        # Verify final state
        remaining_agents = progressive_agent_manager.get_all_agents()
        logger.info(f"🏁 Final count: {len(remaining_agents)} agents remaining")
        
        for agent in remaining_agents:
            logger.info(f"   - {agent.id}: '{agent.query}' (created: {agent.created_at})")
            
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_agents())
