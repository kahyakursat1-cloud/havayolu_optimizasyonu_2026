"""
Aviation SI Unit Utility: Ensures all internal calculations use metric (kg, m, s, N) 
while supporting conversion to/from standard aviation units (lbs, knots, feet).
"""

class AviationUnits:
    # --- Distance ---
    @staticmethod
    def nm_to_km(nm): return nm * 1.852
    @staticmethod
    def km_to_nm(km): return km / 1.852
    
    # --- Altitude ---
    @staticmethod
    def ft_to_m(ft): return ft * 0.3048
    @staticmethod
    def m_to_ft(m): return m / 0.3048
    
    # --- Weight / Mass ---
    @staticmethod
    def lb_to_kg(lb): return lb * 0.453592
    @staticmethod
    def kg_to_lb(kg): return kg / 0.453592
    
    # --- Speed ---
    @staticmethod
    def kt_to_kmh(kt): return kt * 1.852
    @staticmethod
    def kmh_to_kt(kmh): return kmh / 1.852
    
    # --- Fuel ---
    @staticmethod
    def gal_to_lt(gal): return gal * 3.78541
    @staticmethod
    def lt_to_gal(lt): return lt / 3.78541
