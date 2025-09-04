import React, { useState } from "react";

interface PipelineResult {
  extracted: any;
  policy_decision: any;
  summary: any;
}

export default function Chatbot() {
  const [billFile, setBillFile] = useState<File | null>(null);
  const [policyFile, setPolicyFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => {
    // Generate a unique session ID
    return 'session_' + Math.random().toString(36).substr(2, 9);
  });

  const uploadDocument = async (file: File, documentType: string) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("file_type", documentType.toLowerCase());
    formData.append("session_id", sessionId);

    const res = await fetch("http://localhost:8080/upload-document", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${localStorage.getItem('access_token')}`
      },
      body: formData,
      credentials: "include", // include auth cookies if needed
    });

    if (!res.ok) {
      throw new Error(`Failed to upload ${documentType}`);
    }
    return res.json();
  };

  const sendChatMessage = async (message: string) => {
    const res = await fetch("http://localhost:8080/chat", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ 
        message,
        session_id: sessionId 
      }),
      credentials: "include", // include auth cookies if needed
    });

    if (!res.ok) throw new Error("Chat request failed");
    return res.json();
  };

  const handleSubmit = async () => {
    if (!billFile || !policyFile) {
      setError("Please upload both files.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Upload documents
      const billResult = await uploadDocument(billFile, "invoice");
      const policyResult = await uploadDocument(policyFile, "policy");

      console.log("Uploaded bill:", billResult);
      console.log("Uploaded policy:", policyResult);

      // Send chat message
      const chatResponse = await sendChatMessage(
        "Please analyze my uploaded documents"
      );

      setResult(chatResponse);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">MedClaim Chatbot</h1>

      <div className="mb-4">
        <label className="block mb-2 font-medium">Medical Bill PDF</label>
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setBillFile(e.target.files?.[0] || null)}
        />
      </div>

      <div className="mb-4">
        <label className="block mb-2 font-medium">Policy PDF</label>
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setPolicyFile(e.target.files?.[0] || null)}
        />
      </div>

      <button
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? "Processing..." : "Submit"}
      </button>

      {error && <p className="text-red-500 mt-4">{error}</p>}

      {result && (
        <div className="mt-6 space-y-4">
          <div>
            <h2 className="font-bold">Extracted Fields</h2>
            <pre className="bg-gray-100 p-2 rounded overflow-x-auto">
              {JSON.stringify(result.extracted, null, 2)}
            </pre>
          </div>

          <div>
            <h2 className="font-bold">Policy Decision</h2>
            <pre className="bg-gray-100 p-2 rounded overflow-x-auto">
              {JSON.stringify(result.policy_decision, null, 2)}
            </pre>
          </div>

          <div>
            <h2 className="font-bold">Summary</h2>
            <pre className="bg-gray-100 p-2 rounded overflow-x-auto">
              {JSON.stringify(result.summary, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
