"""
Test cases for agent service functionality
"""
import pytest
import json
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime

from agent_service import AgentService


class TestAgentService:
    """Test AgentService class functionality."""
    
    def test_init_success(self):
        """Test successful AgentService initialization."""
        with patch('agent_service.root_agent'), \
             patch('agent_service.document_analyzer_agent'), \
             patch('agent_service.coverage_analyzer_agent'), \
             patch('agent_service.chat_assistant_agent'), \
             patch('agent_service.claim_form_agent'), \
             patch('agent_service.Runner') as mock_runner, \
             patch('agent_service.InMemorySessionService'):
            
            mock_runner.return_value = Mock()
            
            service = AgentService()
            
            assert service.agents is not None
            assert service.session_service is not None
            assert service.app_name == "medclaim_ai"
    
    def test_init_failure(self):
        """Test AgentService initialization failure."""
        with patch('agent_service.root_agent', side_effect=Exception("Agent error")):
            service = AgentService()
            
            # When initialization fails, agents should still be initialized but empty
            assert service.agents is not None
            assert service.runners == {}
            assert service.session_service is None
    
    @pytest.mark.asyncio
    async def test_process_document_success(self, db_session, test_user, test_document):
        """Test successful document processing."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": True,
            "content": '{"policy_number": "POL123", "insurer_name": "Test Insurance"}'
        }) as mock_agent:
            result = await service.process_document(
                "test.pdf", "policy", test_user.id, db_session, test_document.id
            )
            
            assert result["success"] is True
            assert "policy_number" in result["data"]
            assert result["data"]["policy_number"] == "POL123"
    
    @pytest.mark.asyncio
    async def test_process_document_failure(self, db_session, test_user, test_document):
        """Test document processing failure."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": False,
            "error": "Processing failed"
        }) as mock_agent:
            result = await service.process_document(
                "test.pdf", "policy", test_user.id, db_session, test_document.id
            )
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_chat_with_agent_success(self, db_session, test_session):
        """Test successful chat with agent."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": True,
            "content": "Hello! How can I help you with your insurance claim?"
        }) as mock_agent:
            result = await service.chat_with_agent(
                "Hello", test_session.id, db_session
            )
            
            assert result["success"] is True
            assert "response" in result
            assert "Hello! How can I help you" in result["response"]
    
    @pytest.mark.asyncio
    async def test_chat_with_agent_failure(self, db_session, test_session):
        """Test chat with agent failure."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": False,
            "error": "Chat failed"
        }) as mock_agent:
            result = await service.chat_with_agent(
                "Hello", test_session.id, db_session
            )
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_generate_claim_form_success(self, db_session, test_session):
        """Test successful claim form generation."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": True,
            "content": '{"form_data": {"patient_name": "John Doe", "policy_number": "POL123"}}'
        }) as mock_agent:
            result = await service.generate_claim_form(
                test_session.id, db_session
            )
            
            assert result["success"] is True
            assert "form_data" in result
            assert result["form_data"]["patient_name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_generate_claim_form_failure(self, db_session, test_session):
        """Test claim form generation failure."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": False,
            "error": "Form generation failed"
        }) as mock_agent:
            result = await service.generate_claim_form(
                test_session.id, db_session
            )
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_calculate_coverage_success(self, db_session, test_session):
        """Test successful coverage calculation."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": True,
            "content": '{"coverage_amount": 500000, "deductible": 10000, "copay_percentage": 20}'
        }) as mock_agent:
            result = await service.calculate_coverage(
                test_session.id, db_session
            )
            
            assert result["success"] is True
            assert "coverage_amount" in result
            assert result["coverage_amount"] == 500000
    
    @pytest.mark.asyncio
    async def test_calculate_coverage_failure(self, db_session, test_session):
        """Test coverage calculation failure."""
        service = AgentService()
        
        with patch.object(service, '_run_agent_async', return_value={
            "success": False,
            "error": "Coverage calculation failed"
        }) as mock_agent:
            result = await service.calculate_coverage(
                test_session.id, db_session
            )
            
            assert result["success"] is False
            assert "error" in result
    
    def test_extract_structured_data_success(self):
        """Test successful structured data extraction."""
        service = AgentService()
        
        json_content = '{"policy_number": "POL123", "insurer_name": "Test Insurance"}'
        result = service._extract_structured_data(json_content, "policy")
        
        assert result["success"] is True
        assert result["data"]["policy_number"] == "POL123"
        assert result["data"]["insurer_name"] == "Test Insurance"
    
    def test_extract_structured_data_invalid_json(self):
        """Test structured data extraction with invalid JSON."""
        service = AgentService()
        
        invalid_json = "not a json string"
        result = service._extract_structured_data(invalid_json, "policy")
        
        assert result["success"] is False
        assert "error" in result