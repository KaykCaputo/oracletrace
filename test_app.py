import time

def process_data():
    """Main processing function"""
    time.sleep(0.05)
    calculate_results()

def calculate_results():
    """Calculation function"""
    time.sleep(0.05)

def test_function():
    """Test function that should be filtered"""
    time.sleep(0.03)

def test_another():
    """Another test function"""
    time.sleep(0.02)

def main():
    for _ in range(2):
        process_data()
    
    # These should be filtered when using --ignore "test_.*"
    test_function()
    test_another()

if __name__ == "__main__":
    main()
