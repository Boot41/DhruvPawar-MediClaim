#!/usr/bin/env python3
"""
Test script to verify PDF form filling functionality.
"""

from form_automation_tools import fill_local_pdf_tool, get_smart_coordinates

def test_pdf_filling():
    """Test PDF filling with real data and smart coordinates."""
    print("🔍 Testing PDF Form Filling")
    print("-" * 40)
    
    # Sample user data
    user_data = {
        "patient_name": "John Doe",
        "policy_number": "SH123456789",
        "total_cost": "18000",
        "hospital_name": "Apollo Hospital",
        "admission_date": "2024-01-15",
        "phone_number": "9876543210"
    }
    
    vendor = "Star Health Insurance"
    output_file = "./test_filled_form.pdf"
    
    print(f"Vendor: {vendor}")
    print(f"User data: {len(user_data)} fields")
    print(f"Output file: {output_file}")
    print()
    
    # Test the filling function
    result = fill_local_pdf_tool(vendor, user_data, output_file)
    
    if result.get("success"):
        print("✅ PDF filling successful!")
        print(f"   Message: {result['message']}")
        print(f"   Output: {result['filled_pdf_path']}")
        
        if "coordinates_used" in result:
            print("   Coordinates used:")
            for field, coords in result["coordinates_used"].items():
                print(f"     {field}: {coords}")
        
        # Check if file was actually created
        import os
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"   File size: {file_size} bytes")
            
            if file_size > 1000:  # Reasonable size check
                print("✅ Output file looks good!")
            else:
                print("⚠️  Output file seems too small")
        else:
            print("❌ Output file not found")
            
    else:
        print(f"❌ PDF filling failed: {result.get('error')}")
    
    print()

def test_smart_coordinates():
    """Test smart coordinate generation."""
    print("🎯 Testing Smart Coordinate Generation")
    print("-" * 40)
    
    user_data = {
        "patient_name": "John Doe",
        "policy_number": "SH123456789",
        "total_cost": "18000"
    }
    
    pdf_path = "./claim_forms/star_health.pdf"
    
    try:
        coordinates = get_smart_coordinates(pdf_path, user_data)
        print("✅ Smart coordinates generated:")
        for field, coords in coordinates.items():
            print(f"   {field}: x={coords[0]}, y={coords[1]}, page={coords[2]}")
    except Exception as e:
        print(f"❌ Smart coordinate generation failed: {e}")
    
    print()

if __name__ == "__main__":
    test_smart_coordinates()
    test_pdf_filling()
