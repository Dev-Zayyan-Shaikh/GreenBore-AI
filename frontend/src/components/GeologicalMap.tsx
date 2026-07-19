import { useState } from "react";

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
}

interface GeologicalMapProps {
  logs: Record3D[];
  activeBorehole: string;
  onSelectBorehole: (name: string, modifiedLogs?: Record3D[]) => void;
}

interface Well {
  name: string;
  x: number;
  y: number;
  status: "Drilled - Success" | "Drilled - Dry" | "Proposed";
  elevation: number;
}

const ROCK_COLORS: { [key: string]: string } = {
  Claystone: "#64748b",
  Sandstone: "#eab308",
  Limestone: "#fef08a",
  Shale: "#78350f",
  Granite: "#475569",
  Default: "#94a3b8",
};

export const GeologicalMap: React.FC<GeologicalMapProps> = ({
  logs,
  activeBorehole,
  onSelectBorehole,
}) => {
  const [selectedWells, setSelectedWells] = useState<string[]>([activeBorehole]);
  const [hoveredWell, setHoveredWell] = useState<Well | null>(null);

  const wells: Well[] = [
    { name: "BH-01 (Discovery)", x: 150, y: 140, status: "Drilled - Success", elevation: 120 },
    { name: "BH-02 (North Ridge)", x: 380, y: 80, status: "Drilled - Success", elevation: 145 },
    { name: "BH-03 (East Crest)", x: 520, y: 220, status: "Drilled - Dry", elevation: 110 },
    { name: "BH-04 (Deep Valley)", x: 260, y: 280, status: "Proposed", elevation: 95 },
  ];

  // Helper to generate simulated shifts in geological layers to show dynamic cross-sections
  const getShiftedLogs = (baseLogs: Record3D[], wellName: string): Record3D[] => {
    let shift = 0;
    if (wellName.includes("North Ridge")) shift = 10.0; // deeper layers
    if (wellName.includes("East Crest")) shift = -5.0;  // shallower layers
    if (wellName.includes("Deep Valley")) shift = 25.0; // very deep layers

    if (shift === 0) return baseLogs;

    return baseLogs.map((log) => {
      // Find stratum for shifted depth
      const targetDepth = Math.max(0, Math.min(baseLogs[baseLogs.length - 1].depth, log.depth + shift));
      const match = baseLogs.find((l) => Math.abs(l.depth - targetDepth) < 0.5) || log;
      return {
        ...log,
        rock_type: match.rock_type,
        has_water: match.has_water,
        is_fractured: match.is_fractured,
      };
    });
  };

  const handleWellClick = (well: Well) => {
    onSelectBorehole(well.name, getShiftedLogs(logs, well.name));
    
    // Toggle well selection for cross-section
    if (selectedWells.includes(well.name)) {
      if (selectedWells.length > 1) {
        setSelectedWells(selectedWells.filter((w) => w !== well.name));
      }
    } else {
      setSelectedWells([...selectedWells.slice(-1), well.name]); // Keep at most 2 wells selected
    }
  };

  // Compile cross-section layers between the two selected wells
  const renderCrossSection = () => {
    if (selectedWells.length < 2 || logs.length === 0) {
      return (
        <div className="w-full h-full flex items-center justify-center text-slate-500 font-mono text-xs border border-dashed border-slate-800 rounded bg-slate-950/20">
          Select two borehole markers on the GIS map to render a Geological Cross-Section.
        </div>
      );
    }

    const wellA = wells.find((w) => w.name === selectedWells[0]) || wells[0];
    const wellB = wells.find((w) => w.name === selectedWells[1]) || wells[1];

    const logsA = getShiftedLogs(logs, wellA.name);
    const logsB = getShiftedLogs(logs, wellB.name);

    // Compute layers at well A
    const layersA: { rockType: string; start: number; end: number }[] = [];
    let currentA = { rockType: logsA[0].rock_type, start: logsA[0].depth, end: logsA[0].depth };
    logsA.forEach((l) => {
      if (l.rock_type === currentA.rockType) currentA.end = l.depth;
      else {
        layersA.push({ ...currentA });
        currentA = { rockType: l.rock_type, start: l.depth, end: l.depth };
      }
    });
    layersA.push({ ...currentA });

    // Compute layers at well B
    const layersB: { rockType: string; start: number; end: number }[] = [];
    let currentB = { rockType: logsB[0].rock_type, start: logsB[0].depth, end: logsB[0].depth };
    logsB.forEach((l) => {
      if (l.rock_type === currentB.rockType) currentB.end = l.depth;
      else {
        layersB.push({ ...currentB });
        currentB = { rockType: l.rock_type, start: l.depth, end: l.depth };
      }
    });
    layersB.push({ ...currentB });

    const totalDepth = logs[logs.length - 1].depth;
    
    const CS_WIDTH = 480;
    const CS_HEIGHT = 180;
    const padding = 20;

    const scaleY = (CS_HEIGHT - 2 * padding) / totalDepth;
    const getCS_Y = (depth: number, elevation: number) => {
      // Adjust relative vertical position based on terrain elevation difference
      const maxElev = Math.max(wellA.elevation, wellB.elevation);
      const elevOffset = (maxElev - elevation) * 0.4; // 1m elevation = 0.4px offset
      return padding + depth * scaleY + elevOffset;
    };

    // Draw connecting polygons for geological layers between Well A (x = padding) and Well B (x = CS_WIDTH - padding)
    // We map matching rock types or simple sequential slices
    const polygons: React.ReactNode[] = [];

    const numSlices = 20;
    for (let s = 0; s < numSlices; s++) {
      const startDepth = (s / numSlices) * totalDepth;
      const endDepth = ((s + 1) / numSlices) * totalDepth;

      const yA1 = getCS_Y(startDepth, wellA.elevation);
      const yA2 = getCS_Y(endDepth, wellA.elevation);
      const yB1 = getCS_Y(startDepth, wellB.elevation);
      const yB2 = getCS_Y(endDepth, wellB.elevation);

      // Determine rock type at mid depth
      const midDepth = (startDepth + endDepth) / 2;
      const recA = logsA.find((l) => l.depth >= midDepth) || logsA[logsA.length - 1];
      // Interpolated color boundary
      const colorA = ROCK_COLORS[recA.rock_type] || ROCK_COLORS.Default;


      // Draw two triangular slices or one quad to handle rock type changes smoothly
      const points = `${padding},${yA1} ${CS_WIDTH - padding},${yB1} ${CS_WIDTH - padding},${yB2} ${padding},${yA2}`;
      
      polygons.push(
        <polygon
          key={`slice-${s}`}
          points={points}
          fill={colorA} // Simple solid fill of source
          opacity={0.65}
          stroke={colorA}
          strokeWidth={0.5}
        />
      );
    }

    return (
      <div className="w-full h-full flex flex-col bg-slate-50 p-3 border border-slate-200 rounded">
        <div className="flex justify-between items-center text-[10px] text-slate-500 font-semibold mb-2">
          <span>GEOLOGICAL CROSS-SECTION DIAGRAM</span>
          <span className="text-blue-600 font-bold">{wellA.name} ── {wellB.name}</span>
        </div>
        <div className="flex-1 flex justify-center items-center">
          <svg width={CS_WIDTH} height={CS_HEIGHT}>
            {/* Background terrain boundary */}
            <rect x={padding} y={0} width={CS_WIDTH - 2 * padding} height={CS_HEIGHT} fill="#f1f5f9" opacity={0.9} />

            {/* Interpolated strata */}
            {polygons}

            {/* Borehole Well A Shaft */}
            <line
              x1={padding}
              y1={getCS_Y(0, wellA.elevation)}
              x2={padding}
              y2={getCS_Y(totalDepth, wellA.elevation)}
              stroke="#475569"
              strokeWidth={3}
            />
            {/* Borehole Well B Shaft */}
            <line
              x1={CS_WIDTH - padding}
              y1={getCS_Y(0, wellB.elevation)}
              x2={CS_WIDTH - padding}
              y2={getCS_Y(totalDepth, wellB.elevation)}
              stroke="#475569"
              strokeWidth={3}
            />

            {/* Well A Label */}
            <text x={padding} y={getCS_Y(0, wellA.elevation) - 5} fill="#475569" fontSize={8} textAnchor="middle" fontWeight="bold">
              {wellA.name.split(" ")[0]} ({wellA.elevation}m)
            </text>
            {/* Well B Label */}
            <text x={CS_WIDTH - padding} y={getCS_Y(0, wellB.elevation) - 5} fill="#475569" fontSize={8} textAnchor="middle" fontWeight="bold">
              {wellB.name.split(" ")[0]} ({wellB.elevation}m)
            </text>
          </svg>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full h-full bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col font-sans">
      {/* Header Panel */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-xs">
        <div>
          <h3 className="font-semibold text-slate-800">GIS Terrain & Borehole Location Map</h3>
          <p className="text-slate-400 text-[10px]">Select Borehole markers to inspect logging profiles</p>
        </div>
        <div className="bg-white px-2 py-1 border border-slate-200 text-[10px] rounded text-slate-600 shadow-sm">
          Active well: <span className="text-blue-600 font-bold">{activeBorehole}</span>
        </div>
      </div>

      {/* GIS Grid Map */}
      <div className="flex-1 min-h-[220px] bg-slate-50 relative flex items-center justify-center p-4">
        {/* Terrain Topographical Map Grid (svg-rendered background) */}
        <svg width="100%" height="100%" className="max-w-[600px] aspect-[2/1] border border-slate-200 rounded bg-white shadow-sm">
          {/* Contour Lines Simulation */}
          <path d="M 0,50 Q 150,150 300,100 T 600,120" fill="none" stroke="#e2e8f0" strokeWidth={0.8} />
          <path d="M 0,100 Q 200,200 400,120 T 600,180" fill="none" stroke="#e2e8f0" strokeWidth={0.8} />
          <path d="M 0,150 Q 250,220 450,160 T 600,240" fill="none" stroke="#e2e8f0" strokeWidth={0.8} />
          <path d="M 0,200 Q 300,250 500,200 T 600,280" fill="none" stroke="#e2e8f0" strokeWidth={0.8} />

          {/* Coordinate grid lines */}
          <line x1={150} y1={0} x2={150} y2={300} stroke="#f1f5f9" strokeDasharray="3,3" />
          <line x1={300} y1={0} x2={300} y2={300} stroke="#f1f5f9" strokeDasharray="3,3" />
          <line x1={450} y1={0} x2={450} y2={300} stroke="#f1f5f9" strokeDasharray="3,3" />
          <line x1={0} y1={100} x2={600} y2={100} stroke="#f1f5f9" strokeDasharray="3,3" />
          <line x1={0} y1={200} x2={600} y2={200} stroke="#f1f5f9" strokeDasharray="3,3" />

          {/* Connecting Line between cross-section selection */}
          {selectedWells.length === 2 && (() => {
            const wellA = wells.find((w) => w.name === selectedWells[0])!;
            const wellB = wells.find((w) => w.name === selectedWells[1])!;
            return (
              <line
                x1={wellA.x}
                y1={wellA.y}
                x2={wellB.x}
                y2={wellB.y}
                stroke="#3b82f6"
                strokeWidth={1.5}
                strokeDasharray="4,4"
              />
            );
          })()}

          {/* Well Markers */}
          {wells.map((well) => {
            const isActive = activeBorehole === well.name;
            const isCSSelected = selectedWells.includes(well.name);
            const markerColor =
              well.status === "Drilled - Success"
                ? "#22c55e"
                : well.status === "Drilled - Dry"
                ? "#ef4444"
                : "#a855f7";

            return (
              <g
                key={well.name}
                transform={`translate(${well.x}, ${well.y})`}
                className="cursor-pointer group"
                onClick={() => handleWellClick(well)}
                onPointerOver={() => setHoveredWell(well)}
                onPointerOut={() => setHoveredWell(null)}
              >
                {/* Selection highlight ring */}
                {(isActive || isCSSelected) && (
                  <circle
                    r={14}
                    fill="none"
                    stroke={isActive ? "#3b82f6" : "#93c5fd"}
                    strokeWidth={1.5}
                    className="animate-pulse"
                  />
                )}
                {/* Well point dot */}
                <circle r={6} fill={markerColor} />
                <circle r={2} fill="#ffffff" />
                {/* Well short label text */}
                <text
                  x={10}
                  y={4}
                  fill={isActive ? "#2563eb" : "#64748b"}
                  fontSize={8}
                  fontWeight={isActive ? "bold" : "normal"}
                  className="font-semibold select-none"
                >
                  {well.name.split(" ")[0]}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Well Inspector Hover panel */}
        {hoveredWell && (
          <div className="absolute top-4 left-4 bg-white border border-slate-200 p-2.5 rounded shadow-lg text-[10px] text-slate-600 w-44 pointer-events-none z-10">
            <div className="font-bold text-slate-800 mb-0.5">{hoveredWell.name}</div>
            <div>Status: <span className="font-semibold">{hoveredWell.status}</span></div>
            <div>Elevation: <span className="font-semibold">{hoveredWell.elevation}m MSL</span></div>
            <div>Coords: <span className="font-mono text-slate-400">{hoveredWell.x * 10}E, {hoveredWell.y * 10}N</span></div>
          </div>
        )}
      </div>

      {/* Cross-section Render block */}
      <div className="px-4 pb-4 flex-shrink-0">
        {renderCrossSection()}
      </div>
    </div>
  );
};
export default GeologicalMap;
