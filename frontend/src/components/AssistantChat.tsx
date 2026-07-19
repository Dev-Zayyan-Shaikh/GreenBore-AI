import { useState, useRef, useEffect } from "react";

interface Citation {
  title: string;
  category: string;
  content_preview: string;
}

interface Message {
  sender: "user" | "assistant";
  text: string;
  citations?: Citation[];
  loading?: boolean;
}

interface Record3D {
  depth: number;
  rock_type: string;
  density: number;
  porosity: number;
  resistivity: number;
  gamma_ray: number;
  sonic_travel_time: number;
  has_water: boolean;
  is_fractured: boolean;
  prediction?: boolean;
  confidence?: number;
}

interface AssistantChatProps {
  logs: Record3D[];
  predictionDepthIndex: number | null;
  activeModelId: string | null;
}

const renderMarkdown = (text: string) => {
  // 1. Escaping basic HTML to prevent XSS
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // 2. Headings
  html = html.replace(/^### (.*$)/gim, '<h4 class="font-bold text-slate-800 text-xs mt-3 mb-1 uppercase tracking-wider border-b border-slate-100 pb-0.5">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 class="font-bold text-slate-800 text-sm mt-4 mb-1.5 border-b border-slate-200 pb-1">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 class="font-bold text-slate-900 text-base mt-5 mb-2">$1</h2>');

  // 3. Bold text (**text** -> <strong>text</strong>)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-slate-900">$1</strong>');

  // 4. Bullet lists (- and *)
  html = html.replace(/^\s*[-\*]\s+(.*$)/gim, '<li class="ml-4 list-disc text-slate-700 my-0.5">$1</li>');

  // 5. Code blocks or inline code
  html = html.replace(/`(.*?)`/g, '<code class="font-mono bg-slate-150 px-1 rounded text-[11px] text-rose-600 font-bold">$1</code>');

  // 6. Horizontal rules
  html = html.replace(/^---$/gim, '<hr class="my-3 border-slate-200" />');

  // 7. Parse lines to handle tables (+/- and |) and empty spacings
  const lines = html.split("\n");
  const processedLines: string[] = [];
  let inPre = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    const isTableLine = trimmed.startsWith("+") || trimmed.startsWith("|");

    if (isTableLine) {
      if (!inPre) {
        processedLines.push('<pre class="font-mono text-[10px] bg-slate-100 p-2.5 rounded border border-slate-200 overflow-x-auto my-2 text-slate-600 leading-tight">');
        inPre = true;
      }
      processedLines.push(line);
    } else {
      if (inPre) {
        processedLines.push("</pre>");
        inPre = false;
      }

      if (!trimmed) {
        processedLines.push('<div class="h-2"></div>');
      } else if (trimmed.startsWith("<h") || trimmed.startsWith("<li") || trimmed.startsWith("<hr")) {
        processedLines.push(line);
      } else {
        processedLines.push(`<p class="my-1.5 text-slate-700 leading-relaxed">${line}</p>`);
      }
    }
  }
  if (inPre) {
    processedLines.push("</pre>");
  }

  return (
    <div 
      className="markdown-body space-y-1 text-slate-700 font-sans" 
      dangerouslySetInnerHTML={{ __html: processedLines.join("\n") }} 
    />
  );
};

export const AssistantChat: React.FC<AssistantChatProps> = ({
  logs,
  predictionDepthIndex,
  activeModelId,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "assistant",
      text: "Welcome to the GreenBore AI Geological Support System. I can query research literature, well standards, and explain machine learning prediction profiles. Ask a question or trigger an explanation for the active depth segment.",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeRecord = predictionDepthIndex !== null ? logs[predictionDepthIndex] : null;

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    // Add user message
    const newMsg: Message = { sender: "user", text };
    setMessages((prev) => [...prev, newMsg]);
    setInputValue("");

    // Add loading assistant placeholder
    const loadingMsg: Message = { sender: "assistant", text: "Processing search...", loading: true };
    setMessages((prev) => [...prev, loadingMsg]);

    try {
      const response = await fetch("http://localhost:8000/api/v1/assistant/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, k: 3 }),
      });

      if (!response.ok) throw new Error("Assistant response error.");
      const result = await response.json();

      setMessages((prev) => [
        ...prev.filter((m) => !m.loading),
        { sender: "assistant", text: result.answer, citations: result.citations },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev.filter((m) => !m.loading),
        {
          sender: "assistant",
          text: `Error connecting to RAG pipeline: ${e.message || "Endpoint error"}. Check if backend is running.`,
        },
      ]);
    }
  };

  // Trigger XAI prediction explanation request
  const handleExplainPrediction = async () => {
    if (!activeRecord) return;


    const loadingMsg: Message = { sender: "assistant", text: "Analyzing sensor telemetry and generating explainable AI (XAI) profile...", loading: true };
    
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: `Explain prediction at depth ${activeRecord.depth}m` },
      loadingMsg,
    ]);

    try {
      // Build PredictRequest format matching what backend expects
      const sensorData = {
        density: activeRecord.density,
        porosity: activeRecord.porosity,
        resistivity: activeRecord.resistivity,
        gamma_ray: activeRecord.gamma_ray,
        sonic_travel_time: activeRecord.sonic_travel_time,
        // Mock MA5 and ratios for request compatibility
        density_ma5: activeRecord.density,
        porosity_ma5: activeRecord.porosity,
        resistivity_ma5: activeRecord.resistivity,
        gamma_ray_ma5: activeRecord.gamma_ray,
        sonic_travel_time_ma5: activeRecord.sonic_travel_time,
        porosity_resistivity_ratio: activeRecord.porosity / (activeRecord.resistivity + 1e-5),
        density_porosity_ratio: activeRecord.density / (activeRecord.porosity + 1e-5),
        rock_type_encoded: activeRecord.rock_type === "Claystone" ? 0 : activeRecord.rock_type === "Sandstone" ? 1 : activeRecord.rock_type === "Limestone" ? 2 : activeRecord.rock_type === "Shale" ? 3 : 4,
      };

      const response = await fetch("http://localhost:8000/api/v1/predictions/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sensor_data: sensorData, model_id: activeModelId }),
      });

      if (!response.ok) throw new Error("Explanation API failed.");
      const result = await response.json();

      setMessages((prev) => [
        ...prev.filter((m) => !m.loading),
        { sender: "assistant", text: result.explanation, citations: result.citations },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev.filter((m) => !m.loading),
        { sender: "assistant", text: `XAI pipeline failure: ${e.message || "Backend offline"}` },
      ]);
    }
  };

  // Trigger Drilling Recommendation request
  const handleGetRecommendation = async () => {
    if (!activeRecord) return;

    const loadingMsg: Message = { sender: "assistant", text: "Assembling recommendation report...", loading: true };
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: `Generate Casing & Drilling Recommendation report for depth ${activeRecord.depth}m` },
      loadingMsg,
    ]);

    try {
      const sensorData = {
        density: activeRecord.density,
        porosity: activeRecord.porosity,
        resistivity: activeRecord.resistivity,
        gamma_ray: activeRecord.gamma_ray,
        sonic_travel_time: activeRecord.sonic_travel_time,
        density_ma5: activeRecord.density,
        porosity_ma5: activeRecord.porosity,
        resistivity_ma5: activeRecord.resistivity,
        gamma_ray_ma5: activeRecord.gamma_ray,
        sonic_travel_time_ma5: activeRecord.sonic_travel_time,
        porosity_resistivity_ratio: activeRecord.porosity / (activeRecord.resistivity + 1e-5),
        density_porosity_ratio: activeRecord.density / (activeRecord.porosity + 1e-5),
        rock_type_encoded: activeRecord.rock_type === "Claystone" ? 0 : activeRecord.rock_type === "Sandstone" ? 1 : activeRecord.rock_type === "Limestone" ? 2 : activeRecord.rock_type === "Shale" ? 3 : 4,
      };

      const response = await fetch("http://localhost:8000/api/v1/predictions/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sensor_data: sensorData, model_id: activeModelId }),
      });

      if (!response.ok) throw new Error("Recommendation API failed.");
      const result = await response.json();

      setMessages((prev) => [
        ...prev.filter((m) => !m.loading),
        { sender: "assistant", text: result.report, citations: result.evidence_citations },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev.filter((m) => !m.loading),
        { sender: "assistant", text: `Recommendation pipeline failure: ${e.message || "Backend offline"}` },
      ]);
    }
  };

  return (
    <div className="w-full h-full bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col font-sans text-xs shadow-sm">
      {/* Active depth context toolbar */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-[10px]">
        <div className="text-slate-500 font-semibold">
          RAG DECISION INTELLIGENCE CO-PILOT
        </div>
        {activeRecord ? (
          <div className="flex gap-2">
            <button
              onClick={handleExplainPrediction}
              className="bg-cyan-50 border border-cyan-200 text-cyan-700 hover:bg-cyan-100 px-2 py-0.5 rounded transition shadow-sm"
            >
              Explain {activeRecord.depth.toFixed(1)}m Prediction
            </button>
            <button
              onClick={handleGetRecommendation}
              className="bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 px-2 py-0.5 rounded transition shadow-sm"
            >
              Get Recommendation
            </button>
          </div>
        ) : (
          <span className="text-slate-400">Select a depth on the chart to query XAI explanations</span>
        )}
      </div>

      {/* Messages console */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 leading-relaxed border shadow-sm ${
                msg.sender === "user"
                  ? "bg-slate-100 border-slate-200 text-slate-800 whitespace-pre-line"
                  : "bg-blue-50 border-blue-100 text-slate-800 font-sans"
              }`}
            >
              {msg.loading ? (
                <div className="flex items-center gap-1.5 text-slate-400 animate-pulse">
                  <span>●</span><span>●</span><span>●</span>
                </div>
              ) : msg.sender === "user" ? (
                msg.text
              ) : (
                renderMarkdown(msg.text)
              )}
            </div>

            {/* Citations references */}
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-2 w-full max-w-[85%] flex flex-col gap-1.5">
                <span className="text-[10px] text-slate-400 font-bold">CITATIONS:</span>
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {msg.citations.map((cite, cIdx) => (
                    <div
                      key={cIdx}
                      className="bg-white border border-slate-200 p-2 rounded w-44 flex-shrink-0 text-[10px] shadow-sm"
                    >
                      <div className="text-blue-600 font-bold truncate">{cite.title}</div>
                      <div className="text-[8px] text-slate-400 uppercase tracking-wide mb-1">
                        {cite.category}
                      </div>
                      <div className="text-slate-600 text-[9px] line-clamp-2 leading-normal">
                        {cite.content_preview}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* TextInput box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage(inputValue);
        }}
        className="p-3 bg-white border-t border-slate-200 flex gap-2"
      >
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask geological questions (e.g., 'How to prevent siltation in claystone?')..."
          className="flex-1 bg-slate-50 border border-slate-200 rounded px-3 py-2 text-slate-800 focus:outline-none focus:border-blue-400 transition text-xs"
        />
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition shadow-sm font-semibold"
        >
          Send
        </button>
      </form>
    </div>
  );
};
export default AssistantChat;
