import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utilities import setup_logging
from src.VacationRentalTester import VacationRentalTester

def main():
    # Setup logging
    setup_logging()
    
    # Initialize tester
    tester = VacationRentalTester(
        url='https://www.alojamiento.io/property/apartamentos-centro-col%c3%b3n/BC-189483/', 
        headless=False
    )
    
    # Run all tests
    tester.run_all_tests()
    
    # Generate report
    tester.generate_report()

if __name__ == '__main__':
    main()
