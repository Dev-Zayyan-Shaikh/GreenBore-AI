import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Database,
  Layers,
  Settings,
  HelpCircle,
  TrendingUp,
  FolderOpen,
  Cpu,
  RefreshCw,
  CheckCircle2,
  AlertTriangle
} from "lucide-react";

interface HealthResponse {
  status: string;
  env: string;
  database: string;
}

const fetchHealth = async (): Promise<HealthResponse> => {
  const response = await fetch("/api/v1/health");
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }
  return response.json();
};

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const { data: health, isLoading, error, refetch } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 10000 // refetch every 10s
  });

  const isConnected = !error && health?.status === "healthy";

  return (
    <div className="flex h-screen bg-[#0b0f19] text-slate-100 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-[#0d1424] border-r border-slate-800/60 flex flex-col justify-between">
        <div>
          {/* Logo Header */}
          <div className="h-16 flex items-center px-6 border-b border-slate-800/60 gap-3">
            <span className="text-2xl">💧</span>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                GreenBore AI
              </h1>
              <p className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">
                Borehole Intelligence
              </p>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="p-4 space-y-1.5">
            {[
              { id: "dashboard", label: "Dashboard", icon: Activity },
              { id: "datasets", label: "Datasets", icon: FolderOpen },
              { id: "experiments", label: "Experiments", icon: TrendingUp },
              { id: "models", label: "Model Registry", icon: Cpu },
              { id: "knowledge", label: "Knowledge Base", icon: Layers }
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-slate-800/80 text-cyan-400 shadow-lg shadow-cyan-900/10 border-l-2 border-cyan-400"
                      : "text-slate-400 hover:bg-slate-800/30 hover:text-slate-200"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer Settings */}
        <div className="p-4 border-t border-slate-800/60 space-y-1.5">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:bg-slate-800/30 hover:text-slate-200">
            <Settings className="w-4 h-4" />
            Settings
          </button>
          <div className="px-4 py-2 flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-800/40 mt-2 pt-2">
            <span>v0.1.0 (Phase 1)</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header Status Bar */}
        <header className="h-16 bg-[#0c1322]/80 backdrop-blur-md border-b border-slate-800/60 px-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2 py-1 rounded bg-slate-800/80 text-cyan-400">
              Active Phase: 1
            </span>
          </div>

          {/* Database & Backend Connectivity Panel */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Backend Status:</span>
              {isLoading ? (
                <span className="flex items-center gap-1.5 text-amber-400 font-medium animate-pulse">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Checking
                </span>
              ) : isConnected ? (
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Online
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-rose-400 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5" /> Disconnected
                </span>
              )}
            </div>

            <button
              onClick={() => refetch()}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
              title="Refresh Connection"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
          {/* Welcome Dashboard Banner */}
          <section className="bg-gradient-to-br from-slate-900 to-[#0e1628] border border-slate-800/60 p-6 rounded-2xl relative overflow-hidden shadow-2xl">
            <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
            
            <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
              Subsurface Exploration Dashboard
            </h2>
            <p className="text-slate-400 text-sm mt-1 max-w-xl">
              Intelligent geological exploratory analysis engine. Core backend database mappings and frontend React components initialized.
            </p>
          </section>

          {/* Cards Metrics Row */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* System Infrastructure Status */}
            <div className="bg-[#0e1526]/80 border border-slate-800/60 p-5 rounded-xl flex flex-col justify-between h-36">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">System Integration</h3>
                  <p className="text-xl font-bold mt-1 text-slate-100">Dockerized Engine</p>
                </div>
                <div className="p-2 bg-slate-800/60 rounded-lg text-cyan-400">
                  <Activity className="w-5 h-5" />
                </div>
              </div>
              <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>FastAPI + Nginx Services Active</span>
              </div>
            </div>

            {/* Database Mappings Card */}
            <div className="bg-[#0e1526]/80 border border-slate-800/60 p-5 rounded-xl flex flex-col justify-between h-36">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Database Pool</h3>
                  <p className="text-xl font-bold mt-1 text-slate-100">PostgreSQL + pgvector</p>
                </div>
                <div className="p-2 bg-slate-800/60 rounded-lg text-emerald-400">
                  <Database className="w-5 h-5" />
                </div>
              </div>
              <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-2">
                <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                <span>DB Connection: {isConnected ? "Active" : "Offline"}</span>
              </div>
            </div>

            {/* Development Pipeline Info */}
            <div className="bg-[#0e1526]/80 border border-slate-800/60 p-5 rounded-xl flex flex-col justify-between h-36">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Roadmap Status</h3>
                  <p className="text-xl font-bold mt-1 text-slate-100">Infrastructure Base</p>
                </div>
                <div className="p-2 bg-slate-800/60 rounded-lg text-amber-400">
                  <Layers className="w-5 h-5" />
                </div>
              </div>
              <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-2">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span>Next up: Geological Simulation Engine (Phase 2)</span>
              </div>
            </div>
          </section>

          {/* Subsurface Layout Visualizer Grid */}
          <section className="bg-[#0e1526]/80 border border-slate-800/60 p-6 rounded-xl">
            <h3 className="text-sm font-bold border-b border-slate-800/60 pb-3 text-slate-300">
              Subsurface Exploration Visualizer
            </h3>
            
            {/* Visualizer Frame */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-6">
              <div className="lg:col-span-3 h-64 bg-[#0a0d17] rounded-xl border border-slate-800/80 flex flex-col justify-between p-6 relative overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/10 via-transparent to-transparent"></div>
                <div className="flex justify-between items-start z-10">
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 tracking-wide uppercase">Borehole Profile Visualization</h4>
                    <p className="text-slate-500 text-[11px] mt-0.5">Synthetic log mapping simulation frame</p>
                  </div>
                  <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400 font-semibold uppercase">
                    Interactive Preview
                  </span>
                </div>
                
                {/* Mock geological stratum layers */}
                <div className="space-y-2 mt-4 z-10 flex-1 flex flex-col justify-center">
                  <div className="h-6 bg-amber-900/20 border border-amber-950/40 rounded flex items-center justify-between px-3 text-[10px] text-amber-400">
                    <span>Stratum A: Claystone Layer (0m - 12m)</span>
                    <span>Density: 2.1 g/cm³</span>
                  </div>
                  <div className="h-6 bg-slate-700/20 border border-slate-800/40 rounded flex items-center justify-between px-3 text-[10px] text-slate-400">
                    <span>Stratum B: Sandstone Stratum (12m - 34m)</span>
                    <span>Density: 2.3 g/cm³</span>
                  </div>
                  <div className="h-6 bg-cyan-900/20 border border-cyan-950/40 rounded flex items-center justify-between px-3 text-[10px] text-cyan-400">
                    <span>Stratum C: Fracture Water-Bearing zone (34m - 50m)</span>
                    <span>Density: 1.9 g/cm³</span>
                  </div>
                </div>

                <div className="text-[11px] text-slate-500 border-t border-slate-800/40 pt-2 flex justify-between items-center z-10">
                  <span>Stratum Model registry: placeholder (Awaiting Phase 2)</span>
                  <span>Sensor Depth: 50m Max</span>
                </div>
              </div>

              {/* Exploration Summary Info panel */}
              <div className="bg-[#0c1221] rounded-xl border border-slate-800/80 p-5 flex flex-col justify-between">
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-slate-400 tracking-wide uppercase">Platform Details</h4>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500">API Gateway:</span>
                      <span className="font-semibold text-slate-300">FastAPI</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500">UI Engine:</span>
                      <span className="font-semibold text-slate-300">Vite + React</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500">State:</span>
                      <span className="font-semibold text-slate-300">Zustand</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-500">Client:</span>
                      <span className="font-semibold text-slate-300">React Query</span>
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-800/60 pt-4 mt-4">
                  <div className="flex items-center gap-2 p-2.5 rounded bg-cyan-950/20 border border-cyan-900/40 text-[11px] text-cyan-400">
                    <HelpCircle className="w-4 h-4 shrink-0" />
                    <span>Explore API Swagger docs at <strong>/docs</strong>.</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
