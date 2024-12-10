import os
import pandas as pd

class TestReportGenerator:
    def __init__(self, output_folder="test_results"):
        self.output_folder = output_folder
        self.results = {}

    def add_test_results(self, test_name, results):
        """Add results for a specific test to the dictionary."""
        self.results[test_name] = results
    
    def generate_report(self):
        """Generate a consolidated report with multiple sheets for each test."""
        try:
            os.makedirs(self.output_folder, exist_ok=True)
            report_file = os.path.join(self.output_folder, "consolidated_test_report.xlsx")
            
            with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
                # Add each test results as a separate sheet
                for test_name, test_results in self.results.items():
                    if test_results:  # Only write non-empty results
                        df = pd.DataFrame(test_results)
                        df.to_excel(writer, index=False, sheet_name=test_name)
            
            print(f"Consolidated report saved to {report_file}")
        except Exception as e:
            print(f"Error generating report: {e}")
