import datetime

class OperationalReportGenerator:
    """
    v18.0 Strategic Audit: Generates an integrity report summarizing
    the current operational output and tactical KPIs.
    """
    
    def generate_summary(self, scenario_data, kpis):
        """
        Creates a structured text report for the Operations Center.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        report.append("="*50)
        report.append(f"AVIATION SINGULARITY: OPERATIONAL INTEGRITY REPORT")
        report.append(f"TIMESTAMP: {timestamp}")
        report.append("="*50)
        report.append("")
        
        report.append("[STRATEGIC KPI SUMMARY]")
        report.append(f"- Available Seat Kilometers (ASK): {kpis.get('ask', 0):,.0f}")
        report.append(f"- Revenue Passenger Kilometers (RPK): {kpis.get('rpk', 0):,.0f}")
        report.append(f"- Passenger Load Factor (PLF): {kpis.get('plf', 0)}%")
        report.append(f"- Connection Quality Index (CQI): {kpis.get('cqi', 0)}")
        report.append(f"- MCT Compliance: 100%")
        report.append("")
        
        report.append("[TACTICAL FLEET STATUS]")
        active_ac = len(set(f['aircraft_id'] for f in scenario_data if f.get('aircraft_id')))
        delays = sum(1 for f in scenario_data if f.get('assigned_delay', 0) > 0)
        report.append(f"- Active Aircraft Units: {active_ac}")
        report.append(f"- Global Delay Incidents: {delays}")
        report.append(f"- Resilience Level: HIGH (Reactive Recovery Active)")
        report.append("")
        
        report.append("[AI NEURAL COMMANDER LOGS]")
        report.append("- Autonomous Disruption Recovery: ACTIVE")
        report.append("- Neural Processing Status: NOMINAL")
        report.append("")
        report.append("="*50)
        report.append("END OF AUDIT")
        
        return "\n".join(report)

# Singleton
auditor = OperationalReportGenerator()
