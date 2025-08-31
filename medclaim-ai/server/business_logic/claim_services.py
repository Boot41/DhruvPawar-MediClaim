import shutil
import uuid
from pathlib import Path
import json
from PIL import Image
import io
import google.generativeai as genai
from schemas import ChatMessage, ChatResponse

# In-memory stores (replace with DB for production)
extracted_documents = {}
conversation_history = {}

# Configure Gemini API elsewhere during app startup
model = genai.GenerativeModel('gemini-1.5-pro')

async def process_uploaded_file(file, user_id: str, upload_dir: Path) -> dict:
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'txt'}
    file_extension = file.filename.split('.')[-1].lower()

    if file_extension not in allowed_extensions:
        raise Exception(f"File type {file_extension} not allowed. Supported: {allowed_extensions}")

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = upload_dir / unique_filename

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process document by type
    if file_extension in ['jpg', 'jpeg', 'png']:
        extracted_data = await process_image_document(file_path)
    elif file_extension == 'pdf':
        extracted_data = await process_pdf_document(file_path)
    else:
        extracted_data = await process_text_document(file_path)

    # Store extracted data
    document_id = str(uuid.uuid4())
    extracted_documents[document_id] = {
        "filename": file.filename,
        "path": str(file_path),
        "type": file_extension,
        "data": extracted_data,
        "user_id": user_id
    }

    return {
        "document_id": document_id,
        "filename": file.filename,
        "extracted_data": extracted_data,
        "message": "Document processed successfully"
    }


async def process_image_document(file_path: Path) -> dict:
    try:
        image = Image.open(file_path)
        prompt = """
        Analyze this medical document and extract the following information in JSON format:
        {
            "document_type": "medical_bill|prescription|lab_report|discharge_summary|other",
            "patient_info": {
                "name": "patient name if found",
                "date_of_birth": "DOB if found",
                "id": "patient ID if found"
            },
            "provider_info": {
                "name": "healthcare provider name",
                "address": "provider address if found",
                "phone": "provider phone if found"
            },
            "date_of_service": "date when service was provided",
            "services": [
                {
                    "description": "service description",
                    "code": "medical code if found",
                    "amount": "cost amount"
                }
            ],
            "total_amount": "total bill amount",
            "diagnosis": "diagnosis or condition if found",
            "medications": ["list of medications if any"],
            "insurance_info": "insurance related information if found",
            "confidence": "your confidence level (0-1) in the extraction accuracy"
        }
        If this is not a medical document, set document_type as "other" and provide a brief description.
        """
        response = model.generate_content([prompt, image])
        try:
            extracted_data = json.loads(response.text.strip())
        except:
            extracted_data = {"document_type": "unknown", "raw_text": response.text, "confidence": 0.5}
        return extracted_data
    except Exception as e:
        return {"error": f"Failed to process image: {str(e)}", "confidence": 0}


async def process_pdf_document(file_path: Path) -> dict:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        page = doc[0]
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        temp_image_path = file_path.parent / f"temp_{uuid.uuid4()}.png"
        image.save(temp_image_path)
        result = await process_image_document(temp_image_path)
        temp_image_path.unlink()
        doc.close()
        return result
    except Exception as e:
        return {"error": f"Failed to process PDF: {str(e)}", "confidence": 0}


async def process_text_document(file_path: Path) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        prompt = f"""
        Analyze this medical text document and extract relevant information:

        {text_content}

        Extract the information in the same JSON format as requested for image documents.
        """
        response = model.generate_content(prompt)
        try:
            extracted_data = json.loads(response.text.strip())
        except:
            extracted_data = {"document_type": "text", "raw_text": response.text, "confidence": 0.5}
        return extracted_data
    except Exception as e:
        return {"error": f"Failed to process text: {str(e)}", "confidence": 0}


async def chat_with_ai_assistant(chat_message: ChatMessage) -> ChatResponse:
    user_id = chat_message.user_id
    message = chat_message.message

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    user_documents = {k: v for k, v in extracted_documents.items() if v.get("user_id") == user_id}

    context = f"""
    You are a helpful health insurance claim assistant. Help users with:
    1. Understanding their medical documents
    2. Estimating claim amounts
    3. Filing insurance claims
    4. Answering questions about coverage

    User's uploaded documents: {user_documents}
    Previous conversation: {conversation_history[user_id][-5:]}

    Current user message: {message}

    Provide helpful, accurate information about health insurance claims.
    If asked about claim estimation, provide a detailed breakdown.
    If documents were uploaded, reference the specific information from them.
    """
    response = model.generate_content(context)

    conversation_history[user_id].extend([
        {"role": "user", "message": message},
        {"role": "assistant", "message": response.text}
    ])

    claim_estimate = None
    if any(keyword in message.lower() for keyword in ['estimate', 'cost', 'coverage', 'claim amount']):
        claim_estimate = await calculate_claim_estimate(user_documents)

    return ChatResponse(
        response=response.text,
        extracted_data=user_documents,
        claim_estimation=claim_estimate
    )


async def calculate_claim_estimate(user_documents: Dict) -> dict:
    try:
        total_amount = 0
        services = []
        for doc_id, doc_data in user_documents.items():
            extracted = doc_data.get("data", {})
            if "total_amount" in extracted:
                try:
                    amount_str = str(extracted["total_amount"]).replace("$", "").replace(",", "")
                    amount = float(amount_str) if amount_str.replace(".", "").isdigit() else 0
                    total_amount += amount
                except:
                    pass
            if "services" in extracted:
                services.extend(extracted["services"])

        coverage_percentage = 0.8
        deductible = 1000
        copay = 25
        covered_amount = max(0, (total_amount - deductible) * coverage_percentage)
        patient_responsibility = total_amount - covered_amount + copay

        return {
            "total_amount": total_amount,
            "covered_amount": covered_amount,
            "deductible": deductible,
            "copay": copay,
            "patient_responsibility": patient_responsibility,
            "coverage_percentage": coverage_percentage * 100,
            "services_count": len(services)
        }
    except Exception as e:
        return {"error": f"Failed to calculate estimate: {str(e)}"}


def get_claim_data(claim_id: str) -> dict:
    return extracted_documents.get(claim_id, None)


async def get_estimate_for_user(user_id: str) -> dict:
    user_documents = {k: v for k, v in extracted_documents.items() if v.get("user_id") == user_id}
    if not user_documents:
        return None
    return await calculate_claim_estimate(user_documents)
