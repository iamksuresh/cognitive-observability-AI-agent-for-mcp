"""
Enhanced Conversation Correlator.

Improved correlation system that reads user prompts from the quick_log.py
system and correlates them with MCP interactions for accurate reporting.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedConversationCorrelator:
    """
    Enhanced correlator that reads user prompts from multiple sources
    and correlates them with MCP interactions for accurate reporting.
    """
    
    def __init__(self):
        """Initialize the enhanced correlator."""
        self.user_prompts_file = Path.home() / ".cursor" / "user_prompts.jsonl"
        self.correlation_window_minutes = 5  # Match prompts within 5 minutes
        
    def load_recent_user_prompts(self, hours_back: float = 24) -> List[Dict[str, Any]]:
        """Load recent user prompts from the log file."""
        if not self.user_prompts_file.exists():
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        recent_prompts = []
        
        try:
            with open(self.user_prompts_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                        
                        if entry_time >= cutoff_time:
                            recent_prompts.append(entry)
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(f"Skipping invalid prompt entry: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error reading user prompts file: {e}")
            return []
        
        return sorted(recent_prompts, key=lambda x: x['timestamp'])
    
    def correlate_user_prompt_with_interaction(
        self, 
        interaction: Dict[str, Any], 
        user_prompts: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Correlate an MCP interaction with the most likely user prompt.
        
        Args:
            interaction: MCP interaction data
            user_prompts: List of recent user prompts
            
        Returns:
            The correlated user prompt or None
        """
        if not user_prompts:
            return None
            
        # Get interaction timestamp
        try:
            interaction_time = datetime.fromisoformat(
                interaction.get('timestamp', '').replace('Z', '+00:00')
            )
        except (ValueError, TypeError):
            return None
        
        # Find prompts within correlation window
        correlation_window = timedelta(minutes=self.correlation_window_minutes)
        candidate_prompts = []
        
        for prompt_entry in user_prompts:
            try:
                prompt_time = datetime.fromisoformat(
                    prompt_entry['timestamp'].replace('Z', '+00:00')
                )
                
                # Check if prompt is before interaction and within window
                time_diff = interaction_time - prompt_time
                if timedelta(0) <= time_diff <= correlation_window:
                    candidate_prompts.append({
                        'prompt': prompt_entry['user_prompt'],
                        'time_diff': time_diff.total_seconds(),
                        'timestamp': prompt_entry['timestamp']
                    })
                    
            except (ValueError, KeyError):
                continue
        
        if not candidate_prompts:
            return None
        
        # Return the most recent prompt before the interaction
        best_match = min(candidate_prompts, key=lambda x: x['time_diff'])
        
        logger.debug(
            f"Correlated interaction at {interaction.get('timestamp')} "
            f"with prompt: '{best_match['prompt'][:50]}...' "
            f"(time diff: {best_match['time_diff']:.1f}s)"
        )
        
        return best_match['prompt']
    
    def enhance_interactions_with_user_prompts(
        self, 
        interactions: List[Dict[str, Any]], 
        hours_back: float = 24
    ) -> List[Dict[str, Any]]:
        """
        Enhance MCP interactions with correlated user prompts.
        
        Args:
            interactions: List of MCP interactions
            hours_back: How many hours back to look for user prompts
            
        Returns:
            Enhanced interactions with user_query field populated
        """
        user_prompts = self.load_recent_user_prompts(hours_back)
        
        if not user_prompts:
            logger.warning("No user prompts found for correlation")
            return interactions
        
        enhanced_interactions = []
        correlation_stats = {"total": len(interactions), "correlated": 0}
        
        for interaction in interactions:
            enhanced_interaction = interaction.copy()
            
            # Try to correlate with user prompt
            correlated_prompt = self.correlate_user_prompt_with_interaction(
                interaction, user_prompts
            )
            
            if correlated_prompt:
                enhanced_interaction['user_query'] = correlated_prompt
                enhanced_interaction['correlation_method'] = 'time_based_manual_log'
                correlation_stats["correlated"] += 1
            else:
                # Keep existing user_query or mark as unknown
                if 'user_query' not in enhanced_interaction:
                    enhanced_interaction['user_query'] = "Unknown"
                enhanced_interaction['correlation_method'] = 'none'
            
            enhanced_interactions.append(enhanced_interaction)
        
        # Log correlation statistics
        success_rate = (correlation_stats["correlated"] / correlation_stats["total"]) * 100
        logger.info(
            f"Conversation correlation: {correlation_stats['correlated']}/{correlation_stats['total']} "
            f"({success_rate:.1f}% success rate)"
        )
        
        return enhanced_interactions
    
    def get_correlation_status(self) -> Dict[str, Any]:
        """Get current correlation system status."""
        user_prompts = self.load_recent_user_prompts(hours_back=1)
        
        return {
            "user_prompts_file_exists": self.user_prompts_file.exists(),
            "recent_prompts_count": len(user_prompts),
            "correlation_window_minutes": self.correlation_window_minutes,
            "latest_prompt": user_prompts[-1]['user_prompt'] if user_prompts else None,
            "latest_prompt_time": user_prompts[-1]['timestamp'] if user_prompts else None
        } 