#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for multi-partner functionality
Testing with יובל רוכמן and various partner combinations
"""

def parse_multiple_partners(partner_names_string):
    """Parse multiple partner names from a single string field"""
    if not partner_names_string or partner_names_string.strip() == '':
        return []
    
    print(f"🔍 Parsing partners from: '{partner_names_string}'")
    
    # Common separators for multiple names
    separators = [',', '&', '+', ' ו ', ' and ', '\n', ';']
    
    # Start with the original string
    names = [partner_names_string]
    
    # Split by each separator
    for separator in separators:
        new_names = []
        for name in names:
            split_names = [n.strip() for n in name.split(separator) if n.strip()]
            new_names.extend(split_names)
        names = new_names
        if len(names) > 1:
            print(f"   After splitting by '{separator}': {names}")
    
    # Filter out empty strings and duplicates
    unique_names = []
    for name in names:
        cleaned_name = name.strip()
        if cleaned_name and cleaned_name not in unique_names:
            unique_names.append(cleaned_name)
    
    print(f"✅ Final parsed partner names: {unique_names}")
    return unique_names

def test_multi_partner_scenarios():
    """Test various multi-partner scenarios"""
    
    print("=" * 60)
    print("🧪 TESTING MULTI-PARTNER FUNCTIONALITY")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        # Single partner (Hebrew name)
        "יובל רוכמן",
        
        # Multiple partners with comma
        "יובל רוכמן, שרה כהן",
        
        # Multiple partners with Hebrew 'and' (ו)
        "יובל רוכמן ו שרה כהן",
        
        # Multiple partners with ampersand
        "יובל רוכמן & שרה כהן",
        
        # Multiple partners with plus
        "יובל רוכמן + שרה כהן",
        
        # Three partners with different separators
        "יובל רוכמן, שרה כהן & דני לוי",
        
        # Mixed Hebrew and English
        "יובל רוכמן, Sarah Cohen",
        
        # With extra spaces
        "  יובל רוכמן  ,  שרה כהן  ",
        
        # With semicolon
        "יובל רוכמן; שרה כהן",
        
        # With newlines
        "יובל רוכמן\nשרה כהן",
        
        # Empty string
        "",
        
        # Single name with spaces
        "יובל רוכמן  ",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Input: '{test_case}'")
        result = parse_multiple_partners(test_case)
        print(f"Result: {result}")
        print(f"Partner count: {len(result)}")
        print("-" * 40)

def simulate_registration_status():
    """Simulate how the bot would handle registration status for multiple partners"""
    print("\n" + "=" * 60)
    print("🤖 SIMULATING BOT RESPONSE FOR MULTI-PARTNER REGISTRATION")
    print("=" * 60)
    
    # Simulate a user with multiple partners
    user_partners = "יובל רוכמן, שרה כהן"
    parsed_partners = parse_multiple_partners(user_partners)
    
    print(f"\n👤 User's partners: {user_partners}")
    print(f"🔍 Parsed into: {parsed_partners}")
    
    # Simulate checking registration status
    print("\n📊 Checking registration status...")
    
    # Mock registered users (in real system, this would come from Google Sheets)
    registered_users = [
        "דני לוי",
        "שרה כהן",  # This partner is registered
        "מיכל אברהם",
        "יונתן דוד"
        # יובל רוכמן is missing - not registered
    ]
    
    registered_partners = []
    missing_partners = []
    
    for partner in parsed_partners:
        print(f"   Checking: {partner}")
        if partner in registered_users:
            print(f"   ✅ Found: {partner}")
            registered_partners.append(partner)
        else:
            print(f"   ❌ Missing: {partner}")
            missing_partners.append(partner)
    
    print(f"\n📈 Registration Status Summary:")
    print(f"✅ Registered partners: {registered_partners}")
    print(f"❌ Missing partners: {missing_partners}")
    print(f"🔄 All partners registered: {len(missing_partners) == 0}")
    
    # Simulate bot messages
    print(f"\n🤖 Bot would send this message:")
    if missing_partners:
        if len(missing_partners) == 1:
            print(f"⚠️ הפרטנר שלך {missing_partners[0]} עוד לא נרשם. אנא הזכר לו להירשם לאירוע.")
        else:
            missing_names = ', '.join(missing_partners)
            print(f"⚠️ הפרטנרים הבאים שלך עוד לא נרשמו: {missing_names}. אנא הזכר להם להירשם לאירוע.")
    else:
        print("🎉 כל הפרטנרים שלך נרשמו בהצלחה!")

if __name__ == "__main__":
    test_multi_partner_scenarios()
    simulate_registration_status() 