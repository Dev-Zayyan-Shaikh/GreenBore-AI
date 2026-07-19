import React, { useState } from "react";

interface Dataset {
  dataset_name: string;
  created_at: string;
  size_bytes: number;
  has_csv: boolean;
  has_json: boolean;
  has_parquet: boolean;
}

interface DataGeneratorProps {
  datasets: Dataset[];
  onFetchDatasets: () => Promise<void>;
  onSelectDataset: (name: string) => void;
  activeDataset: string;
}

export const DataGenerator: React.FC<DataGeneratorProps> = ({
  datasets,
  onFetchDatasets,
  onSelectDataset,
  activeDataset,
}) => {
  const [depth, setDepth] = useState("100.0");
  const [interval, setInterval] = useState("0.5");
  const [noise, setNoise] = useState("0.2"); // sensor noise factor scale
  const [generating, setGenerating] = useState(false);

  const handleGenerateData = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      // Build a premium geological configuration (default layered strata)
      const config = {
        total_depth: parseFloat(depth) || 100.0,
        interval: parseFloat(interval) || 0.5,
        layers: [
          {
            rock_type: "Sandstone",
            depth_start: 0.0,
            depth_end: 35.0,
            density: 2.3,
            porosity: 0.25,
            base_resistivity: 150.0,
            base_gamma: 35.0,
            base_sonic: 80.0,
          },
          {
            rock_type: "Claystone",
            depth_start: 35.0,
            depth_end: 55.0,
            density: 2.2,
            porosity: 0.15,
            base_resistivity: 8.0,
            base_gamma: 105.0,
            base_sonic: 125.0,
          },
          {
            rock_type: "Limestone",
            depth_start: 55.0,
            depth_end: 80.0,
            density: 2.65,
            porosity: 0.12,
            base_resistivity: 650.0,
            base_gamma: 15.0,
            base_sonic: 52.0,
          },
          {
            rock_type: "Granite",
            depth_start: 80.0,
            depth_end: parseFloat(depth) || 100.0,
            density: 2.8,
            porosity: 0.02,
            base_resistivity: 1200.0,
            base_gamma: 45.0,
            base_sonic: 40.0,
          },
        ],
        fractures: [
          { depth: 22.0, width: 2.0, dip_angle: 30.0 },
          { depth: 68.0, width: 4.5, dip_angle: 45.0 },
        ],
        water_zones: [
          { depth_start: 15.0, depth_end: 30.0, flow_rate: 3.5, salinity: 800.0 },
          { depth_start: 65.0, depth_end: 78.0, flow_rate: 6.0, salinity: 3000.0 },
        ],
        noise: {
          gamma_std: parseFloat(noise) * 2.0,
          resistivity_std: parseFloat(noise) * 0.5,
          porosity_std: parseFloat(noise) * 0.02,
          density_std: parseFloat(noise) * 0.03,
          sonic_std: parseFloat(noise) * 0.8,
        },
      };

      const response = await fetch("http://localhost:8000/api/v1/simulation/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (!response.ok) throw new Error("FastAPI simulation failed.");
      const result = await response.json();
      
      alert(`Simulation completed! Generated ${result.records_count} records. File prefix: ${result.dataset_name}`);
      await onFetchDatasets();
      onSelectDataset(result.dataset_name);
    } catch (e: any) {
      alert(`Simulation failed: ${e.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadFile = (datasetName: string, format: "csv" | "json" | "parquet") => {
    const url = `http://localhost:8000/api/v1/simulation/datasets/${datasetName}/download?format=${format}`;
    window.open(url, "_blank");
  };

  return (
    <div className="w-full h-full bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col font-sans text-xs shadow-sm">
      {/* Header Panel */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-slate-800">Borehole Logs Data Simulation Platform</h3>
          <p className="text-slate-400 text-[10px]">Configure geological parameters and export datasets</p>
        </div>
      </div>

      <div className="flex-1 p-4 grid grid-cols-1 md:grid-cols-3 gap-4 overflow-y-auto bg-slate-55/50">
        {/* Simulator controls */}
        <div className="bg-white border border-slate-200 p-4 rounded flex flex-col md:col-span-1 shadow-sm">
          <h4 className="text-slate-800 font-bold text-sm mb-3 border-b border-slate-200 pb-1.5">
            Simulator Engine Configurations
          </h4>

          <form onSubmit={handleGenerateData} className="space-y-4 flex-1 flex flex-col">
            <div>
              <label className="text-[10px] text-slate-500 font-bold block mb-1">TOTAL DEPTH (METERS)</label>
              <input
                type="number"
                value={depth}
                onChange={(e) => setDepth(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 focus:outline-none focus:border-blue-400 transition"
                min="10"
                max="200"
              />
            </div>

            <div>
              <label className="text-[10px] text-slate-500 font-bold block mb-1">INTERVAL RESOLUTION (STEPS)</label>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 focus:outline-none focus:border-blue-400 transition"
              >
                <option value="0.2">High Res (0.2m intervals)</option>
                <option value="0.5">Standard (0.5m intervals)</option>
                <option value="1.0">Low Res (1.0m intervals)</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-500 font-bold block mb-1">GAUSSIAN SENSOR NOISE FACTOR</label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.1"
                  value={noise}
                  onChange={(e) => setNoise(e.target.value)}
                  className="flex-1 accent-blue-600"
                />
                <span className="text-slate-800 font-bold w-8">{noise}</span>
              </div>
            </div>

            {/* Geological Preset Summary text */}
            <div className="bg-slate-50 border border-slate-200 p-2.5 rounded text-[10px] text-slate-500 leading-normal space-y-1">
              <div className="text-slate-700 font-bold">Standard Simulation Preset:</div>
              <div>• 4 lithological layers (Sandstone, Clay, Lime, Granite)</div>
              <div>• 2 geological fracture zones with structural dip</div>
              <div>• 2 water-bearing targets (salinity, hydrostatic pressures)</div>
            </div>

            <div className="flex-1" />

            <button
              type="submit"
              disabled={generating}
              className="w-full bg-blue-600 hover:bg-blue-700 border border-blue-700 text-white py-2.5 rounded font-bold transition disabled:opacity-50 mt-4 shadow-sm"
            >
              {generating ? "Simulating logs..." : "Generate logs & Preprocess"}
            </button>
          </form>
        </div>

        {/* Database export catalog list */}
        <div className="bg-white border border-slate-200 p-4 rounded flex flex-col md:col-span-2 shadow-sm">
          <h4 className="text-slate-800 font-bold text-sm mb-3 border-b border-slate-200 pb-1.5">
            Simulation File Exporter
          </h4>

          {datasets.length === 0 ? (
            <div className="text-slate-400 text-center py-10">No simulated datasets generated yet.</div>
          ) : (
            <div className="space-y-3 overflow-y-auto flex-1 max-h-[360px]">
              {datasets.map((dataset) => {
                const isActive = activeDataset === dataset.dataset_name;
                return (
                  <div
                    key={dataset.dataset_name}
                    className={`border rounded p-3 flex justify-between items-center cursor-pointer transition-all ${
                      isActive ? "border-blue-500/50 bg-blue-50/20 shadow-sm" : "border-slate-200 bg-white hover:bg-slate-50"
                    }`}
                    onClick={() => onSelectDataset(dataset.dataset_name)}
                  >
                    <div className="space-y-1">
                      <div className="text-slate-800 font-bold">{dataset.dataset_name}</div>
                      <div className="text-[10px] text-slate-400">
                        Generated: <span className="text-slate-600 font-semibold">{new Date(dataset.created_at).toLocaleString()}</span> | Size: <span className="text-slate-500 font-semibold">{(dataset.size_bytes / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>

                    {/* Download options */}
                    <div className="flex gap-1.5" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleDownloadFile(dataset.dataset_name, "csv")}
                        className="bg-white hover:bg-slate-50 border border-slate-200 px-2 py-1 rounded text-[10px] text-slate-700 font-bold shadow-sm"
                      >
                        CSV
                      </button>
                      <button
                        onClick={() => handleDownloadFile(dataset.dataset_name, "json")}
                        className="bg-white hover:bg-slate-50 border border-slate-200 px-2 py-1 rounded text-[10px] text-slate-700 font-bold shadow-sm"
                      >
                        JSON
                      </button>
                      <button
                        onClick={() => handleDownloadFile(dataset.dataset_name, "parquet")}
                        className="bg-white hover:bg-slate-50 border border-slate-200 px-2 py-1 rounded text-[10px] text-slate-700 font-bold shadow-sm"
                      >
                        Parquet
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default DataGenerator;
