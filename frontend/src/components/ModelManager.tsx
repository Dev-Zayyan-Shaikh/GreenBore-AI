import { useState, useEffect } from "react";

interface Model {
  model_id: string;
  model_type: "RandomForest" | "XGBoost";
  version: number;
  parameters: any;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
  };
  features: string[];
  created_at: string;
  is_production: boolean;
}

interface Dataset {
  dataset_name: string;
  created_at: string;
  size_bytes: number;
}

interface ModelManagerProps {
  datasets: Dataset[];
  onModelChange: (modelId: string) => void;
}

export const ModelManager: React.FC<ModelManagerProps> = ({ datasets, onModelChange }) => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Training form state
  const [modelType, setModelType] = useState<"RandomForest" | "XGBoost">("RandomForest");
  const [targetDataset, setTargetDataset] = useState("");
  const [nEstimators, setNEstimators] = useState("10");
  const [maxDepth, setMaxDepth] = useState("5");
  const [learningRate, setLearningRate] = useState("0.1"); // for XGBoost

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/api/v1/models");
      if (!response.ok) throw new Error("Failed to load models registry catalog.");
      const data = await response.json();
      setModels(data);
      
      const prodModel = data.find((m: Model) => m.is_production);
      if (prodModel) {
        onModelChange(prodModel.model_id);
      }
    } catch (e: any) {
      setError(e.message || "Failed to load models.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    if (datasets.length > 0 && !targetDataset) {
      setTargetDataset(datasets[0].dataset_name);
    }
  }, [datasets]);

  const handlePromoteToProduction = async (modelId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/models/set-production/${modelId}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to promote model.");
      await fetchModels();
    } catch (e: any) {
      alert(`Promotion error: ${e.message}`);
    }
  };

  const handleTrainModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetDataset) {
      alert("Please select or generate a training dataset first.");
      return;
    }

    setTraining(true);
    try {
      // Build hyperparameters
      const hyperparameters: any = {};
      if (modelType === "RandomForest") {
        hyperparameters.n_estimators = parseInt(nEstimators) || 10;
        hyperparameters.max_depth = parseInt(maxDepth) || 5;
      } else {
        hyperparameters.n_estimators = parseInt(nEstimators) || 10;
        hyperparameters.max_depth = parseInt(maxDepth) || 5;
        hyperparameters.learning_rate = parseFloat(learningRate) || 0.1;
      }

      const response = await fetch("http://localhost:8000/api/v1/models/train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_type: modelType,
          hyperparameters,
          dataset_name: targetDataset,
          set_prod: true, // auto-set to production for convenience
        }),
      });

      if (!response.ok) throw new Error("Training pipeline execution error.");
      alert("Model trained and registered successfully! Set as active production model.");
      await fetchModels();
    } catch (e: any) {
      alert(`Training error: ${e.message}`);
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="w-full h-full bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col font-sans text-xs shadow-sm">
      {/* Header toolbar */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-slate-800">ML Model Catalog & Registry</h3>
          <p className="text-slate-400 text-[10px]">Monitor and train classifier algorithms</p>
        </div>
        <button
          onClick={fetchModels}
          className="bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 px-2.5 py-1 rounded shadow-sm font-semibold"
        >
          Refresh Catalog
        </button>
      </div>

      <div className="flex-1 p-4 grid grid-cols-1 md:grid-cols-3 gap-4 overflow-y-auto bg-slate-50/50">
        {/* Model training interface */}
        <div className="bg-white border border-slate-200 p-4 rounded flex flex-col md:col-span-1 shadow-sm">
          <h4 className="text-slate-800 font-bold text-sm mb-3 border-b border-slate-200 pb-1.5">
            Train New Model
          </h4>
          
          <form onSubmit={handleTrainModel} className="space-y-4 flex-1 flex flex-col">
            <div>
              <label className="text-[10px] text-slate-500 font-bold block mb-1">MODEL TYPE</label>
              <select
                value={modelType}
                onChange={(e: any) => setModelType(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 focus:outline-none focus:border-blue-400 transition"
              >
                <option value="RandomForest">Random Forest Classifier</option>
                <option value="XGBoost">XGBoost Classifier</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-500 font-bold block mb-1">TRAINING DATASET</label>
              {datasets.length > 0 ? (
                <select
                  value={targetDataset}
                  onChange={(e: any) => setTargetDataset(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 focus:outline-none focus:border-blue-400 transition"
                >
                  {datasets.map((d) => (
                    <option key={d.dataset_name} value={d.dataset_name}>
                      {d.dataset_name} ({(d.size_bytes / 1024).toFixed(1)} KB)
                    </option>
                  ))}
                </select>
              ) : (
                <div className="text-red-600 text-[10px] border border-red-200 bg-red-50 p-2 rounded">
                  No simulated datasets found. Generate data first.
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-slate-500 font-bold block mb-1">ESTIMATORS</label>
                <input
                  type="number"
                  value={nEstimators}
                  onChange={(e) => setNEstimators(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 focus:outline-none focus:border-blue-400 transition"
                  min="1"
                  max="100"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-bold block mb-1">MAX DEPTH</label>
                <input
                  type="number"
                  value={maxDepth}
                  onChange={(e) => setMaxDepth(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 focus:outline-none focus:border-blue-400 transition"
                  min="1"
                  max="20"
                />
              </div>
            </div>

            {modelType === "XGBoost" && (
              <div>
                <label className="text-[10px] text-slate-500 font-bold block mb-1">LEARNING RATE</label>
                <input
                  type="number"
                  step="0.01"
                  value={learningRate}
                  onChange={(e) => setLearningRate(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-800 focus:outline-none focus:border-blue-400 transition"
                  min="0.01"
                  max="1.0"
                />
              </div>
            )}

            <div className="flex-1" />

            <button
              type="submit"
              disabled={training}
              className="w-full bg-blue-600 hover:bg-blue-700 border border-blue-700 text-white py-2.5 rounded font-bold transition disabled:opacity-50 mt-4 shadow-sm"
            >
              {training ? "Executing pipeline..." : "Train & Set Production"}
            </button>
          </form>
        </div>

        {/* Registered models table list */}
        <div className="bg-white border border-slate-200 p-4 rounded flex flex-col md:col-span-2 overflow-x-auto shadow-sm">
          <h4 className="text-slate-800 font-bold text-sm mb-3 border-b border-slate-200 pb-1.5">
            Registered Models List
          </h4>

          {loading ? (
            <div className="text-slate-400 text-center py-10">Scanning model catalog...</div>
          ) : error ? (
            <div className="text-red-500 text-center py-10">{error}</div>
          ) : models.length === 0 ? (
            <div className="text-slate-400 text-center py-10">No models registered yet.</div>
          ) : (
            <div className="space-y-3 overflow-y-auto flex-1 min-h-0">
              {models.map((model) => (
                <div
                  key={model.model_id}
                  className={`border rounded p-3 flex justify-between items-center transition-all ${
                    model.is_production ? "border-blue-500/50 bg-blue-50/20" : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-800 font-bold">{model.model_id}</span>
                      {model.is_production && (
                        <span className="bg-blue-50 text-blue-600 border border-blue-200 text-[8px] font-bold px-1.5 py-0.5 rounded tracking-wide uppercase">
                          Active Production
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      Type: <span className="text-slate-700 font-semibold">{model.model_type}</span> | Registered: <span className="text-slate-500 font-semibold">{new Date(model.created_at).toLocaleString()}</span>
                    </div>
                    
                    {/* Metrics Grid */}
                    <div className="grid grid-cols-4 gap-4 pt-2">
                      <div className="border-r border-slate-200 pr-4">
                        <div className="text-[8px] text-slate-400 font-bold">ACCURACY</div>
                        <div className="text-slate-800 font-bold">{(model.metrics.accuracy * 100).toFixed(1)}%</div>
                      </div>
                      <div className="border-r border-slate-200 pr-4">
                        <div className="text-[8px] text-slate-400 font-bold">PRECISION</div>
                        <div className="text-slate-800 font-bold">{(model.metrics.precision * 100).toFixed(1)}%</div>
                      </div>
                      <div className="border-r border-slate-200 pr-4">
                        <div className="text-[8px] text-slate-400 font-bold">RECALL</div>
                        <div className="text-slate-800 font-bold">{(model.metrics.recall * 100).toFixed(1)}%</div>
                      </div>
                      <div>
                        <div className="text-[8px] text-slate-400 font-bold">F1 SCORE</div>
                        <div className="text-slate-800 font-bold">{(model.metrics.f1 * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                  </div>

                  {!model.is_production && (
                    <button
                      onClick={() => handlePromoteToProduction(model.model_id)}
                      className="bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 px-3 py-1.5 rounded transition text-[10px] font-bold shadow-sm"
                    >
                      Promote
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default ModelManager;
