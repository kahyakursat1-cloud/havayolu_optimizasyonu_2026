import random
import logging

logger = logging.getLogger("AviationSingularity.MarketIntel")

class MarketIntelligenceConnector:
    """
    v20.0 Competitive Intelligence Layer.
    Simulates external GDS (Amadeus/Sabre) and IATA data to identify 
    market gaps where competitors have low capacity.
    """
    def __init__(self):
        # Base market share and competitor capacity per route
        # In a real system, this would fetch from a database or API
        self._route_intelligence = {
            ('IST', 'LHR'): {'competitor_share': 0.65, 'market_demand': 1200, 'yield_quality': 1.2},
            ('IST', 'JFK'): {'competitor_share': 0.45, 'market_demand': 850,  'yield_quality': 1.5},
            ('IST', 'ESB'): {'competitor_share': 0.30, 'market_demand': 2500, 'yield_quality': 0.8},
            ('ADB', 'IST'): {'competitor_share': 0.25, 'market_demand': 1800, 'yield_quality': 0.9},
        }

    def get_competitive_outlook(self, origin, destination) -> dict:
        """
        Returns competitive metrics for a specific O&D pair.
        """
        route = (origin, destination)
        intel = self._route_intelligence.get(route, {
            'competitor_share': random.uniform(0.4, 0.7),
            'market_demand': random.randint(300, 1000),
            'yield_quality': 1.0
        })
        
        # Calculate 'Market Gap' - opportunity for our airline
        # Higher gap means we should prioritize this route to seize market share
        intel['market_gap_index'] = max(0.1, 1.0 - intel['competitor_share'])
        
        return intel

    def enrich_scenario_with_intel(self, df):
        """
        Injects market intelligence into the operational dataframe.
        """
        if df.empty: return df
        
        market_gaps = []
        yield_qualities = []
        
        for _, row in df.iterrows():
            intel = self.get_competitive_outlook(row['origin'], row['destination'])
            market_gaps.append(intel['market_gap_index'])
            yield_qualities.append(intel['yield_quality'])
            
        df['market_gap_index'] = market_gaps
        df['yield_quality_index'] = yield_qualities
        return df

market_intel = MarketIntelligenceConnector()
