#!/usr/bin/env python3
"""
Simple engine test - verifies the RPM fix is working
"""

import time
from engine.simulator import MainEngineSimulator

def test_engine():
    """Test that engine RPM increases when started"""
    print("🔧 Testing Engine RPM Fix")
    print("=" * 40)
    
    try:
        # Create simulator
        simulator = MainEngineSimulator()
        print(f"✅ Simulator created")
        print(f"Initial: RPM={simulator.current_rpm}, Status={simulator.status}, Temp={simulator.current_temp:.1f}°C")
        
        # Start engine
        print("\n🚀 Starting engine...")
        simulator.running = True
        
        # Test progression
        success = False
        for i in range(5):
            simulator.calculate_engine_parameters()
            simulator.update_modbus_registers()
            
            print(f"Step {i+1}: RPM={simulator.current_rpm:.0f}, "
                  f"Temp={simulator.current_temp:.1f}°C, "
                  f"Status={simulator.status}, "
                  f"Load={simulator.current_load}%")
            
            if simulator.current_rpm > 0:
                print(f"\n✅ SUCCESS! RPM is increasing from 0 to {simulator.current_rpm:.0f}")
                print("The RPM fix is working correctly!")
                success = True
                break
            
            time.sleep(0.1)
        
        if not success:
            print("\n❌ FAILED: RPM is still 0")
            return False
        
        # Test stop
        print(f"\n🛑 Testing engine stop...")
        simulator.running = False
        
        for i in range(2):
            simulator.calculate_engine_parameters()
            simulator.update_modbus_registers()
            print(f"Stop step {i+1}: RPM={simulator.current_rpm:.0f}, Status={simulator.status}")
            time.sleep(0.1)
        
        print("✅ Engine stop test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success = test_engine()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 ENGINE TEST PASSED!")
        print("\nThe RPM fix is working correctly.")
        print("Your engine will now properly start and increase RPM.")
        print("\n📝 Next steps:")
        print("1. Start backend: python app.py")
        print("2. Start frontend: cd frontend && npm start")
        print("3. Open browser: http://localhost:3000")
        print("4. Click 'START ENGINE' and watch RPM increase!")
        print("5. Try the new Settings page to configure parameters")
    else:
        print("❌ ENGINE TEST FAILED!")
        print("There are still issues with the engine functionality.")

if __name__ == "__main__":
    main() 