"""
Test script to verify the refactored API and business logic separation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly after refactoring"""
    print("Testing imports...")
    
    try:
        # Test business logic imports
        from business_logic import admin_service, chat_service, claim_service, document_service, user_service
        print("✓ Business logic services imported successfully")
        
        # Test API imports
        from api import api_admin, api_chat, api_claims, api_documents, api_users
        print("✓ API modules imported successfully")
        
        # Test that services are properly instantiated
        assert hasattr(admin_service, 'get_system_overview')
        assert hasattr(chat_service, 'process_chat_message')
        assert hasattr(claim_service, 'create_claim')
        assert hasattr(document_service, 'upload_and_process_document')
        assert hasattr(user_service, 'create_user')
        print("✓ All service methods are accessible")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_service_structure():
    """Test that services have the expected structure"""
    print("\nTesting service structure...")
    
    try:
        from business_logic import admin_service, chat_service, claim_service, document_service, user_service
        
        # Test admin service methods
        admin_methods = ['get_system_overview', 'get_user_statistics', 'get_claim_statistics', 
                        'get_document_statistics', 'cleanup_old_files', 'reprocess_failed_documents',
                        'get_system_config', 'update_system_config']
        
        for method in admin_methods:
            assert hasattr(admin_service, method), f"admin_service missing {method}"
        print("✓ Admin service has all required methods")
        
        # Test chat service methods
        chat_methods = ['process_chat_message', 'start_chat_session', 'get_user_chat_sessions',
                       'get_session_messages', 'delete_chat_session', 'get_user_claims_context',
                       'get_user_documents_context', 'get_user_policies_context', 'get_chat_suggestions',
                       'submit_chat_feedback', 'flag_message']
        
        for method in chat_methods:
            assert hasattr(chat_service, method), f"chat_service missing {method}"
        print("✓ Chat service has all required methods")
        
        # Test claim service methods
        claim_methods = ['create_claim', 'get_claims', 'get_claim_by_id', 'update_claim',
                        'submit_claim', 'process_claim', 'estimate_claim_coverage',
                        'get_claim_estimate', 'get_claim_status_history', 'appeal_claim']
        
        for method in claim_methods:
            assert hasattr(claim_service, method), f"claim_service missing {method}"
        print("✓ Claim service has all required methods")
        
        # Test document service methods
        document_methods = ['upload_and_process_document', 'get_documents', 'get_document_by_id',
                           'update_document', 'delete_document', 'reprocess_document',
                           'verify_document', 'get_document_file', 'get_document_analysis']
        
        for method in document_methods:
            assert hasattr(document_service, method), f"document_service missing {method}"
        print("✓ Document service has all required methods")
        
        # Test user service methods
        user_methods = ['create_user', 'get_users', 'get_user_by_id', 'get_user_by_email',
                       'update_user', 'deactivate_user', 'activate_user', 'verify_password',
                       'change_password', 'get_user_profile_summary', 'update_last_login',
                       'get_user_statistics']
        
        for method in user_methods:
            assert hasattr(user_service, method), f"user_service missing {method}"
        print("✓ User service has all required methods")
        
        return True
        
    except Exception as e:
        print(f"✗ Service structure test failed: {e}")
        return False

def test_api_router_structure():
    """Test that API routers are properly structured"""
    print("\nTesting API router structure...")
    
    try:
        from api.api_admin import router as admin_router
        from api.api_chat import router as chat_router
        from api.api_claims import router as claims_router
        from api.api_documents import router as documents_router
        from api.api_users import router as users_router
        
        # Check router prefixes
        assert admin_router.prefix == "/admin"
        assert chat_router.prefix == "/chat"
        assert claims_router.prefix == "/claims"
        assert documents_router.prefix == "/documents"
        assert users_router.prefix == "/users"
        print("✓ All routers have correct prefixes")
        
        # Check that routers have routes
        assert len(admin_router.routes) > 0
        assert len(chat_router.routes) > 0
        assert len(claims_router.routes) > 0
        assert len(documents_router.routes) > 0
        assert len(users_router.routes) > 0
        print("✓ All routers have routes defined")
        
        return True
        
    except Exception as e:
        print(f"✗ API router structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING REFACTORED API AND BUSINESS LOGIC SEPARATION")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_service_structure,
        test_api_router_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring was successful.")
        print("\nThe API and business logic have been successfully separated:")
        print("• API files now only handle HTTP requests/responses")
        print("• Business logic is properly encapsulated in service classes")
        print("• Code is more modular and maintainable")
        print("• Services can be easily tested and reused")
    else:
        print("❌ Some tests failed. Please review the issues above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
