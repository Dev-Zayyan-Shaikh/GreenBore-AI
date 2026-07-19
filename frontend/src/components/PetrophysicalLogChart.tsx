import React, { useRef } from "react";

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

interface PetrophysicalLogChartProps {
  logs: Record3D[];
  predictionDepthIndex: number | null;
  onSelectDepthIndex: (index: number) => void;
}

export const PetrophysicalLogChart: React.FC<PetrophysicalLogChartProps> = ({
  logs,
  predictionDepthIndex,
  onSelectDepthIndex,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  if (logs.length === 0) {
    return (
      <div className="w-full h-full bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-center text-slate-500 font-mono text-xs">
        No active geological log dataset loaded.
      </div>
    );
  }

  const CHART_HEIGHT = Math.max(600, logs.length * 6); // 6px per sample step
  const totalDepth = logs[logs.length - 1].depth;

  // Max/min values for scaling
  const maxGR = Math.max(...logs.map((d) => d.gamma_ray), 150);
  const minGR = 0;
  
  const maxRES = Math.max(...logs.map((d) => d.resistivity), 1000);
  const minRES = 0.1; // Log scale bottom

  const maxDensity = 3.2;
  const minDensity = 1.8;

  const maxPorosity = 0.5;
  const minPorosity = 0.0;

  const maxSonic = Math.max(...logs.map((d) => d.sonic_travel_time), 140);
  const minSonic = 40;

  // Coordinates helper mappings
  const getX = (val: number, min: number, max: number, width: number) => {
    const ratio = (val - min) / (max - min);
    return Math.max(0, Math.min(width, ratio * width));
  };

  const getLogX = (val: number, min: number, max: number, width: number) => {
    const logVal = Math.log10(Math.max(val, 0.01));
    const logMin = Math.log10(min);
    const logMax = Math.log10(max);
    const ratio = (logVal - logMin) / (logMax - logMin);
    return Math.max(0, Math.min(width, ratio * width));
  };

  const getY = (depth: number) => {
    return (depth / totalDepth) * (CHART_HEIGHT - 40) + 20;
  };

  // Compile line paths
  const grPathPoints: string[] = [];
  const resPathPoints: string[] = [];
  const sonicPathPoints: string[] = [];
  const densityPathPoints: string[] = [];
  const porosityPathPoints: string[] = [];
  const predPathPoints: string[] = [];

  const TRACK_WIDTH = 130;

  logs.forEach((d) => {
    const y = getY(d.depth);
    
    // GR track
    grPathPoints.push(`${getX(d.gamma_ray, minGR, maxGR, TRACK_WIDTH)},${y}`);

    // RES track (Logarithmic scale)
    resPathPoints.push(`${getLogX(d.resistivity, minRES, maxRES, TRACK_WIDTH)},${y}`);

    // Porosity & Density Crossover (Reversed scales on same track)
    porosityPathPoints.push(`${getX(d.porosity, minPorosity, maxPorosity, TRACK_WIDTH)},${y}`);
    densityPathPoints.push(`${getX(d.density, minDensity, maxDensity, TRACK_WIDTH)},${y}`);

    // Sonic Track
    sonicPathPoints.push(`${getX(d.sonic_travel_time, minSonic, maxSonic, TRACK_WIDTH)},${y}`);

    // AI Prediction Confidence (gradient fill or line)
    const confVal = d.prediction ? (d.confidence || 0.85) : 1.0 - (d.confidence || 0.85);
    predPathPoints.push(`${getX(confVal, 0.0, 1.0, TRACK_WIDTH)},${y}`);
  });

  const grPath = `M ${grPathPoints.join(" L ")}`;
  const resPath = `M ${resPathPoints.join(" L ")}`;
  const porosityPath = `M ${porosityPathPoints.join(" L ")}`;
  const densityPath = `M ${densityPathPoints.join(" L ")}`;
  const sonicPath = `M ${sonicPathPoints.join(" L ")}`;
  const predPath = `M ${predPathPoints.join(" L ")}`;

  // Find prediction crossover shaded regions for NPHI-RHOB gas/water presence
  const crossoverPolygons: string[] = [];
  let currentPolygon: string[] = [];
  
  logs.forEach((d) => {
    const y = getY(d.depth);
    const xP = getX(d.porosity, minPorosity, maxPorosity, TRACK_WIDTH);
    const xD = getX(d.density, minDensity, maxDensity, TRACK_WIDTH);

    // Crossover is when porosity is high and density is low (crossover of curves)
    if (xP > xD) {
      currentPolygon.push(`${xP},${y}`);
      currentPolygon.unshift(`${xD},${y}`);
    } else {
      if (currentPolygon.length > 0) {
        crossoverPolygons.push(`M ${currentPolygon.join(" L ")} Z`);
        currentPolygon = [];
      }
    }
  });
  if (currentPolygon.length > 0) {
    crossoverPolygons.push(`M ${currentPolygon.join(" L ")} Z`);
  }

  // Handle clicking on vertical chart to select depth
  const handleChartClick = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!containerRef.current) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickY = e.clientY - rect.top - 20; // 20px offset
    const totalHeight = rect.height - 40;
    const clickedDepth = (clickY / totalHeight) * totalDepth;

    // Find closest index
    let closestIdx = 0;
    let minDiff = Infinity;
    logs.forEach((d, idx) => {
      const diff = Math.abs(d.depth - clickedDepth);
      if (diff < minDiff) {
        minDiff = diff;
        closestIdx = idx;
      }
    });

    onSelectDepthIndex(closestIdx);
  };

  const selectedLog = predictionDepthIndex !== null ? logs[predictionDepthIndex] : null;

  return (
    <div className="w-full h-full bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col font-sans shadow-sm">
      {/* Chart controls/metadata panel */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-xs">
        <div>
          <h3 className="font-semibold text-slate-800">Petrophysical Borehole Log Tracks</h3>
          <p className="text-slate-400 text-[10px]">Standard Multi-Track Geological Formats</p>
        </div>
        {selectedLog && (
          <div className="bg-white border border-slate-200 px-3 py-1.5 rounded flex gap-4 text-[10px] text-slate-600 shadow-sm">
            <div>Depth: <span className="text-blue-600 font-bold">{selectedLog.depth.toFixed(1)}m</span></div>
            <div>Rock: <span className="text-amber-600 font-bold">{selectedLog.rock_type}</span></div>
            <div>RES: <span className="text-red-600 font-bold">{selectedLog.resistivity.toFixed(1)}Ωm</span></div>
            <div>GR: <span className="text-green-600 font-bold">{selectedLog.gamma_ray.toFixed(0)} API</span></div>
            <div>AI: <span className="text-cyan-600 font-bold">{(selectedLog.confidence ? selectedLog.confidence * 100 : 0).toFixed(0)}%</span></div>
          </div>
        )}
      </div>

      {/* Chart Canvas Scrollable container */}
      <div ref={containerRef} className="flex-1 overflow-y-auto p-4 flex justify-center bg-slate-50/50">
        <svg
          width={TRACK_WIDTH * 5 + 180}
          height={CHART_HEIGHT}
          className="cursor-crosshair select-none"
          onClick={handleChartClick}
        >
          {/* Depth Axis Column */}
          <g transform="translate(10, 0)">
            <rect width={50} height={CHART_HEIGHT} fill="#f8fafc" />
            <line x1={50} y1={0} x2={50} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            {logs.filter((_, idx) => idx % 10 === 0).map((d) => (
              <g key={`d-axis-${d.depth}`} transform={`translate(0, ${getY(d.depth)})`}>
                <line x1={40} y1={0} x2={50} y2={0} stroke="#cbd5e1" />
                <text x={35} y={4} fill="#64748b" fontSize={9} textAnchor="end">{d.depth.toFixed(0)}m</text>
              </g>
            ))}
          </g>

          {/* Track 1: Gamma Ray Lithology */}
          <g transform={`translate(${60 + 10}, 0)`}>
            <rect width={TRACK_WIDTH} height={CHART_HEIGHT} fill="#ffffff" />
            <line x1={0} y1={0} x2={0} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            <line x1={TRACK_WIDTH} y1={0} x2={TRACK_WIDTH} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            
            {/* Grid Lines */}
            {[0.25, 0.5, 0.75].map((r) => (
              <line
                key={`gr-grid-${r}`}
                x1={TRACK_WIDTH * r}
                y1={0}
                x2={TRACK_WIDTH * r}
                y2={CHART_HEIGHT}
                stroke="#f1f5f9"
                strokeDasharray="2,4"
              />
            ))}

            {/* Header labels */}
            <rect width={TRACK_WIDTH} height={20} fill="#f1f5f9" opacity={0.9} />
            <text x={TRACK_WIDTH / 2} y={13} fill="#16a34a" fontSize={9} textAnchor="middle" fontWeight="bold">GR (Gamma Ray)</text>

            {/* Log curve */}
            <path d={grPath} fill="none" stroke="#16a34a" strokeWidth={1.5} />
          </g>

          {/* Track 2: Electrical Resistivity */}
          <g transform={`translate(${60 + TRACK_WIDTH + 20}, 0)`}>
            <rect width={TRACK_WIDTH} height={CHART_HEIGHT} fill="#ffffff" />
            <line x1={0} y1={0} x2={0} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            <line x1={TRACK_WIDTH} y1={0} x2={TRACK_WIDTH} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            
            {/* Grid Lines (logarithmic) */}
            {[1, 10, 100].map((v) => (
              <line
                key={`res-grid-${v}`}
                x1={getLogX(v, minRES, maxRES, TRACK_WIDTH)}
                y1={0}
                x2={getLogX(v, minRES, maxRES, TRACK_WIDTH)}
                y2={CHART_HEIGHT}
                stroke="#f1f5f9"
                strokeDasharray="2,4"
              />
            ))}

            {/* Header labels */}
            <rect width={TRACK_WIDTH} height={20} fill="#f1f5f9" opacity={0.9} />
            <text x={TRACK_WIDTH / 2} y={13} fill="#dc2626" fontSize={9} textAnchor="middle" fontWeight="bold">RES (Resistivity)</text>

            {/* Log curve */}
            <path d={resPath} fill="none" stroke="#dc2626" strokeWidth={1.5} />
          </g>

          {/* Track 3: Porosity / Density Crossover */}
          <g transform={`translate(${60 + TRACK_WIDTH * 2 + 30}, 0)`}>
            <rect width={TRACK_WIDTH} height={CHART_HEIGHT} fill="#ffffff" />
            <line x1={0} y1={0} x2={0} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            <line x1={TRACK_WIDTH} y1={0} x2={TRACK_WIDTH} y2={CHART_HEIGHT} stroke="#e2e8f0" />

            {/* Grid Lines */}
            {[0.25, 0.5, 0.75].map((r) => (
              <line
                key={`nphi-grid-${r}`}
                x1={TRACK_WIDTH * r}
                y1={0}
                x2={TRACK_WIDTH * r}
                y2={CHART_HEIGHT}
                stroke="#f1f5f9"
                strokeDasharray="2,4"
              />
            ))}

            {/* Crossover highlighted regions */}
            {crossoverPolygons.map((poly, idx) => (
              <path key={`cross-${idx}`} d={poly} fill="#2563eb" fillOpacity={0.2} />
            ))}

            {/* Header labels */}
            <rect width={TRACK_WIDTH} height={20} fill="#f1f5f9" opacity={0.9} />
            <text x={2} y={13} fill="#d97706" fontSize={8} textAnchor="start" fontWeight="bold">NPHI (Por)</text>
            <text x={TRACK_WIDTH - 2} y={13} fill="#db2777" fontSize={8} textAnchor="end" fontWeight="bold">RHOB (Dens)</text>

            {/* Log curves */}
            <path d={porosityPath} fill="none" stroke="#d97706" strokeWidth={1.2} />
            <path d={densityPath} fill="none" stroke="#db2777" strokeWidth={1.2} />
          </g>

          {/* Track 4: Sonic Travel Time */}
          <g transform={`translate(${60 + TRACK_WIDTH * 3 + 40}, 0)`}>
            <rect width={TRACK_WIDTH} height={CHART_HEIGHT} fill="#ffffff" />
            <line x1={0} y1={0} x2={0} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            <line x1={TRACK_WIDTH} y1={0} x2={TRACK_WIDTH} y2={CHART_HEIGHT} stroke="#e2e8f0" />

            {/* Grid Lines */}
            {[0.25, 0.5, 0.75].map((r) => (
              <line
                key={`dt-grid-${r}`}
                x1={TRACK_WIDTH * r}
                y1={0}
                x2={TRACK_WIDTH * r}
                y2={CHART_HEIGHT}
                stroke="#f1f5f9"
                strokeDasharray="2,4"
              />
            ))}

            {/* Header labels */}
            <rect width={TRACK_WIDTH} height={20} fill="#f1f5f9" opacity={0.9} />
            <text x={TRACK_WIDTH / 2} y={13} fill="#2563eb" fontSize={9} textAnchor="middle" fontWeight="bold">DT (Acoustic Sonic)</text>

            {/* Log curve */}
            <path d={sonicPath} fill="none" stroke="#2563eb" strokeWidth={1.5} />
          </g>

          {/* Track 5: AI Predictions Overlay */}
          <g transform={`translate(${60 + TRACK_WIDTH * 4 + 50}, 0)`}>
            <rect width={TRACK_WIDTH} height={CHART_HEIGHT} fill="#ffffff" />
            <line x1={0} y1={0} x2={0} y2={CHART_HEIGHT} stroke="#e2e8f0" />
            <line x1={TRACK_WIDTH} y1={0} x2={TRACK_WIDTH} y2={CHART_HEIGHT} stroke="#e2e8f0" />

            {/* Render ground-truth water zones as background highlights */}
            {logs.map((d, idx) => {
              if (!d.has_water) return null;
              const y = getY(d.depth);
              const nextY = idx + 1 < logs.length ? getY(logs[idx + 1].depth) : y + 6;
              return (
                <rect
                  key={`gt-water-${idx}`}
                  x={0}
                  y={y}
                  width={TRACK_WIDTH}
                  height={Math.max(1, nextY - y)}
                  fill="#0ea5e9"
                  opacity={0.06}
                />
              );
            })}

            {/* Render AI positive prediction segments as a solid block overlay */}
            {logs.map((d, idx) => {
              const isWater = d.prediction !== undefined ? d.prediction : d.has_water;
              if (!isWater) return null;
              const y = getY(d.depth);
              const nextY = idx + 1 < logs.length ? getY(logs[idx + 1].depth) : y + 6;
              
              // Color intensity scales with model confidence
              const conf = d.confidence || 0.85;
              return (
                <rect
                  key={`ai-water-${idx}`}
                  x={0}
                  y={y}
                  width={TRACK_WIDTH}
                  height={Math.max(1, nextY - y)}
                  fill="#0ea5e9"
                  opacity={0.1 + conf * 0.2}
                />
              );
            })}

            {/* Header labels */}
            <rect width={TRACK_WIDTH} height={20} fill="#f1f5f9" opacity={0.9} />
            <text x={TRACK_WIDTH / 2} y={13} fill="#0891b2" fontSize={9} textAnchor="middle" fontWeight="bold">AI Water Prediction</text>

            {/* Confidence Log Curve (line representing water probability) */}
            <path d={predPath} fill="none" stroke="#0891b2" strokeWidth={1} strokeDasharray="3,3" />
          </g>

          {/* Sync Cursor (depth pointer line across all tracks) */}
          {selectedLog && (
            <g transform={`translate(10, ${getY(selectedLog.depth)})`}>
              <line x1={0} y1={0} x2={TRACK_WIDTH * 5 + 160} y2={0} stroke="#3b82f6" strokeWidth={1.5} />
              <polygon points="-4,-4 -4,4 4,0" fill="#3b82f6" transform="translate(0, 0)" />
              <polygon points="4,-4 4,4 -4,0" fill="#3b82f6" transform={`translate(${TRACK_WIDTH * 5 + 160}, 0)`} />
            </g>
          )}
        </svg>
      </div>
    </div>
  );
};
export default PetrophysicalLogChart;
