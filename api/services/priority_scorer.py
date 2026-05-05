"""
Enhanced Priority Scorer for TAZARA AI Auto-Scheduling System
Calculates comprehensive priority scores for orders based on multiple factors
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedPriorityScorer:
    """Advanced priority scoring system for automatic scheduling"""
    
    def __init__(self):
        self.priority_threshold = 75.0  # Default threshold for auto-scheduling
        
        # Priority factor weights
        self.urgency_weights = {
            'emergency': 40,
            'urgent': 30,
            'priority': 20,
            'standard': 10,
            'normal': 5
        }
        
        self.customer_tier_weights = {
            'platinum': 30,
            'gold': 20,
            'silver': 10,
            'bronze': 5,
            'standard': 2
        }
        
        self.deadline_weights = {
            'critical': 20,    # <= 24 hours
            'urgent': 15,      # <= 3 days
            'high': 10,         # <= 7 days
            'medium': 5,        # <= 14 days
            'low': 2            # > 14 days
        }
        
        self.cargo_value_weights = {
            'very_high': 10,    # > 1,000,000 ZMW
            'high': 5,          # > 500,000 ZMW
            'medium': 2,        # > 100,000 ZMW
            'low': 1             # <= 100,000 ZMW
        }
    
    def calculate_priority_score(self, order: Dict) -> Dict:
        """
        Calculate comprehensive priority score for an order
        
        Args:
            order: Dictionary containing order information
            
        Returns:
            Dictionary with priority score and detailed factors
        """
        try:
            score = 0
            factors = {}
            
            # 1. Urgency Analysis (0-40 points)
            urgency_level, urgency_score = self._calculate_urgency_score(order)
            factors['urgency'] = {
                'level': urgency_level,
                'score': urgency_score,
                'weight': self.urgency_weights.get(urgency_level, 0)
            }
            score += urgency_score
            
            # 2. Customer Tier Analysis (0-30 points)
            customer_tier = self._normalize_customer_tier(order.get('customer_tier', 'standard'))
            tier_score = self.customer_tier_weights.get(customer_tier, 2)
            factors['customer_tier'] = {
                'tier': customer_tier,
                'score': tier_score,
                'weight': self.customer_tier_weights.get(customer_tier, 0)
            }
            score += tier_score
            
            # 3. Deadline Analysis (0-20 points)
            deadline_category, deadline_score = self._calculate_deadline_score(order)
            factors['deadline'] = {
                'category': deadline_category,
                'score': deadline_score,
                'weight': self.deadline_weights.get(deadline_category, 0)
            }
            score += deadline_score
            
            # 4. Cargo Value Analysis (0-10 points)
            value_category, value_score = self._calculate_cargo_value_score(order)
            factors['cargo_value'] = {
                'category': value_category,
                'score': value_score,
                'weight': self.cargo_value_weights.get(value_category, 0)
            }
            score += value_score
            
            # 5. Waiting Time Adjustment (0-15 points)
            waiting_score = self._calculate_waiting_time_adjustment(order)
            factors['waiting_time'] = {
                'hours_waiting': waiting_score['hours'],
                'score': waiting_score['points'],
                'weight': waiting_score['points']
            }
            score += waiting_score['points']
            
            # 6. Special Handling Factors (0-5 points)
            special_score = self._calculate_special_factors(order)
            factors['special_factors'] = {
                'score': special_score,
                'details': special_score
            }
            score += special_score
            
            # Cap at 100
            final_score = min(score, 100)
            
            # Determine if qualifies for auto-scheduling
            qualifies_auto = final_score >= self.priority_threshold
            
            return {
                'order_id': order.get('order_id', ''),
                'priority_score': final_score,
                'urgency_level': urgency_level,
                'customer_tier': customer_tier,
                'deadline_category': deadline_category,
                'qualifies_auto': qualifies_auto,
                'factors': factors,
                'calculated_at': datetime.now().isoformat(),
                'total_possible': 100
            }
            
        except Exception as e:
            logger.error(f"Error calculating priority score for order {order.get('order_id', 'unknown')}: {e}")
            return {
                'order_id': order.get('order_id', ''),
                'priority_score': 0,
                'error': str(e),
                'calculated_at': datetime.now().isoformat()
            }
    
    def _calculate_urgency_score(self, order: Dict) -> tuple:
        """Calculate urgency score based on order ID and metadata"""
        order_id = order.get('order_id', '').lower()
        metadata = order.get('metadata', {})
        
        # Check order ID for urgency keywords
        if 'emergency' in order_id or metadata.get('urgency') == 'emergency':
            return 'emergency', 40
        elif 'urgent' in order_id or metadata.get('urgency') == 'urgent':
            return 'urgent', 30
        elif 'priority' in order_id or metadata.get('urgency') == 'priority':
            return 'priority', 20
        elif 'standard' in order_id or metadata.get('urgency') == 'standard':
            return 'standard', 10
        else:
            return 'normal', 5
    
    def _normalize_customer_tier(self, tier: str) -> str:
        """Normalize customer tier input"""
        tier_normalized = tier.lower().strip()
        
        # Handle various input formats
        if tier_normalized in ['platinum', 'plat', 'platinum_plus']:
            return 'platinum'
        elif tier_normalized in ['gold', 'gold_plus', 'premium']:
            return 'gold'
        elif tier_normalized in ['silver', 'silver_plus', 'standard_plus']:
            return 'silver'
        elif tier_normalized in ['bronze', 'basic', 'economy']:
            return 'bronze'
        else:
            return 'standard'
    
    def _calculate_deadline_score(self, order: Dict) -> tuple:
        """Calculate deadline score based on delivery deadline"""
        deadline_str = order.get('delivery_deadline')
        if not deadline_str:
            return 'low', 2
        
        try:
            if isinstance(deadline_str, str):
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            else:
                deadline = deadline_str
            
            now = datetime.now()
            time_until_deadline = deadline - now
            
            if time_until_deadline.total_seconds() <= 86400:  # <= 24 hours
                return 'critical', 20
            elif time_until_deadline.total_seconds() <= 259200:  # <= 3 days
                return 'urgent', 15
            elif time_until_deadline.total_seconds() <= 604800:  # <= 7 days
                return 'high', 10
            elif time_until_deadline.total_seconds() <= 1209600:  # <= 14 days
                return 'medium', 5
            else:
                return 'low', 2
                
        except Exception as e:
            logger.warning(f"Error parsing deadline for order {order.get('order_id')}: {e}")
            return 'low', 2
    
    def _calculate_cargo_value_score(self, order: Dict) -> tuple:
        """Calculate cargo value score"""
        cargo_value = order.get('cargo_value', 0)
        
        try:
            if cargo_value > 1000000:  # > 1M ZMW
                return 'very_high', 10
            elif cargo_value > 500000:  # > 500K ZMW
                return 'high', 5
            elif cargo_value > 100000:  # > 100K ZMW
                return 'medium', 2
            else:
                return 'low', 1
                
        except (TypeError, ValueError):
            logger.warning(f"Invalid cargo value for order {order.get('order_id')}: {cargo_value}")
            return 'low', 1
    
    def _calculate_waiting_time_adjustment(self, order: Dict) -> Dict:
        """Calculate priority adjustment based on waiting time"""
        created_at_str = order.get('created_at')
        if not created_at_str:
            return {'hours': 0, 'points': 0}
        
        try:
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                created_at = created_at_str
            
            now = datetime.now()
            hours_waiting = (now - created_at).total_seconds() / 3600
            
            # Increase priority for orders waiting too long
            if hours_waiting > 48:  # > 48 hours
                return {'hours': hours_waiting, 'points': 15}
            elif hours_waiting > 24:  # > 24 hours
                return {'hours': hours_waiting, 'points': 10}
            elif hours_waiting > 12:  # > 12 hours
                return {'hours': hours_waiting, 'points': 5}
            else:
                return {'hours': hours_waiting, 'points': 0}
                
        except Exception as e:
            logger.warning(f"Error calculating waiting time for order {order.get('order_id')}: {e}")
            return {'hours': 0, 'points': 0}
    
    def _calculate_special_factors(self, order: Dict) -> int:
        """Calculate special handling factors"""
        score = 0
        order_id = order.get('order_id', '').lower()
        metadata = order.get('metadata', {})
        
        # Government contracts (+3 points)
        if 'government' in order_id or metadata.get('contract_type') == 'government':
            score += 3
        
        # Medical supplies (+2 points)
        if 'medical' in order_id or metadata.get('cargo_category') == 'medical':
            score += 2
        
        # Perishable goods (+1 point)
        if metadata.get('perishable') is True:
            score += 1
        
        # High-security cargo (+1 point)
        if metadata.get('security_level') == 'high':
            score += 1
        
        # Special customer requests (+1 point)
        if metadata.get('special_handling') is True:
            score += 1
        
        # Maximum special factors: 5 points
        return min(score, 5)
    
    def batch_calculate_scores(self, orders: List[Dict]) -> List[Dict]:
        """Calculate priority scores for multiple orders"""
        results = []
        
        for order in orders:
            score_result = self.calculate_priority_score(order)
            results.append(score_result)
        
        # Sort by priority score (descending)
        results.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return results
    
    def get_high_priority_orders(self, orders: List[Dict]) -> List[Dict]:
        """Filter orders that qualify for auto-scheduling"""
        high_priority = []
        
        for order in orders:
            score_result = self.calculate_priority_score(order)
            if score_result.get('qualifies_auto', False):
                high_priority.append(score_result)
        
        return high_priority
    
    def update_priority_for_time(self, orders: List[Dict]) -> List[Dict]:
        """Update priority scores based on waiting time"""
        updated_orders = []
        
        for order in orders:
            # Recalculate with current waiting time
            updated_score = self.calculate_priority_score(order)
            updated_orders.append(updated_score)
        
        return updated_orders
