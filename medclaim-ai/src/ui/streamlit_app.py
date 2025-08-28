import streamlit as st
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.rag_service import MedClaimRAGService
from config.settings import get_settings

# Page configuration
st.set_page_config(
    page_title="MedClaim AI Validator",
    page_icon="🏥",
    layout="wide"
)

# Header
st.title("🏥 MedClaim AI Validator")
st.markdown("**AI-powered medical claim document processing and validation**")
st.caption("Upload medical documents, policies, and claims to extract insights and validate against rules.")

# Initialize settings and service
settings = get_settings()

@st.cache_resource(show_spinner=False)
def get_rag_service():
    """Initialize and cache the RAG service."""
    return MedClaimRAGService()

# Sidebar with settings
with st.sidebar:
    st.header("⚙️ Configuration")
    st.json({
        "embedding_model": settings.embedding_model,
        "ollama_model": settings.ollama_model,
        "collection": settings.collection_name,
        "chunk_size": settings.chunk_size,
        "top_k": settings.top_k
    }, expanded=False)
    
    if st.button("🔄 Reload Service"):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 Workflow")
    st.markdown("""
    1. **Upload** PDF documents
    2. **Process** with AI extraction
    3. **Query** for specific information
    4. **Validate** against policies
    """)

# Initialize service
try:
    service = get_rag_service()
    st.success("✅ RAG Service initialized successfully")
except Exception as e:
    st.error(f"❌ Error initializing service: {str(e)}")
    st.stop()

# Document upload section
st.header("📄 Document Upload & Processing")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_files = st.file_uploader(
        "Upload medical documents (PDF format)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload claim forms, policy documents, medical reports, etc."
    )

with col2:
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} file(s) selected")

# Process uploaded files
if uploaded_files and st.button("🔄 Process Documents", type="primary"):
    progress_bar = st.progress(0)
    status_container = st.container()
    
    # Track uploaded filenames in session state
    if "uploaded_filenames" not in st.session_state:
        st.session_state.uploaded_filenames = set()
    
    results = []
    for i, file in enumerate(uploaded_files):
        with status_container:
            st.write(f"Processing: {file.name}")
        
        # Process the file
        result = service.ingest_pdf(file.getvalue(), file.name)
        results.append(result)
        
        if result["status"] == "success":
            st.session_state.uploaded_filenames.add(file.name)
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    # Show results
    st.header("📊 Processing Results")
    for result in results:
        if result["status"] == "success":
            st.success(f"✅ {result['filename']}: {result['chunks_added']} chunks processed")
        else:
            st.error(f"❌ {result['filename']}: {result['message']}")
    
    # Show session files
    if st.session_state.uploaded_filenames:
        st.info(f"📚 Session documents: {', '.join(sorted(st.session_state.uploaded_filenames))}")

# Query section
st.header("🔍 Query & Analysis")

# Query options
col1, col2 = st.columns([3, 1])

with col1:
    query_input = st.text_area(
        "Ask a question about your documents",
        placeholder="Examples:\n- What is the patient's policy number?\n- What procedures were performed?\n- Are there any missing documents?\n- What is the total claim amount?",
        height=100
    )

with col2:
    restrict_to_session = st.checkbox(
        "🎯 Restrict to uploaded files",
        value=True,
        help="Only search in documents uploaded in this session"
    )
    
    query_button = st.button("🚀 Ask Question", type="primary")

# Process query
if query_button and query_input.strip():
    with st.spinner("🔍 Analyzing documents and generating response..."):
        # Determine filter
        filter_files = None
        if restrict_to_session and "uploaded_filenames" in st.session_state:
            filter_files = list(st.session_state.uploaded_filenames)
        
        # Execute query
        response = service.query(query_input.strip(), filter_filenames=filter_files)
    
    # Display results
    if response["status"] == "success":
        st.subheader("💡 Answer")
        st.write(response["answer"])
        
        # Show sources
        if response["sources"]:
            st.subheader("📚 Sources")
            for i, source in enumerate(response["sources"], 1):
                with st.expander(f"📄 Source {i}: {source['filename']}"):
                    st.write("**Content Preview:**")
                    st.text(source["content"])
                    st.write("**Metadata:**")
                    st.json(source["metadata"], expanded=False)
        else:
            st.info("ℹ️ No specific sources found for this query")
            
        # Show filter info
        if restrict_to_session and filter_files:
            st.caption(f"🎯 Search restricted to: {', '.join(filter_files)}")
    else:
        st.error(f"❌ Query failed: {response['answer']}")

# Footer
st.markdown("---")
st.markdown("""
### 💡 Tips for Better Results
- Upload clear, text-based PDF documents
- Ask specific questions about policy numbers, procedures, amounts, etc.
- Use the session filter to focus on recently uploaded documents
- For complex queries, break them into smaller, specific questions
""")

# System status
with st.expander("🔧 System Status"):
    stats = service.get_document_stats()
    if stats["status"] == "success":
        st.success("✅ Vector database operational")
    else:
        st.error(f"❌ System issue: {stats['message']}")
    
    st.write("**Configuration:**")
    st.json({
        "Embedding Model": settings.embedding_model,
        "LLM Model": settings.ollama_model,
        "Chunk Size": settings.chunk_size,
        "Top K Results": settings.top_k
    })
