import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";

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

interface Subsurface3DViewerProps {
  logs: Record3D[];
  predictionDepthIndex: number | null;
  onSelectDepthIndex: (index: number) => void;
}

const ROCK_COLORS: { [key: string]: string } = {
  Claystone: "#94a3b8", // Slate Gray
  Sandstone: "#fde047", // Soft Gold Yellow
  Limestone: "#cbd5e1", // Light Grey
  Shale: "#d97706",     // Amber Brown
  Granite: "#64748b",   // Granite
  Default: "#e2e8f0",
};

interface GeologicalSceneProps {
  logs: Record3D[];
  predictionDepthIndex: number | null;
  onSelectDepthIndex: (index: number) => void;
  hoveredInfo: any;
  setHoveredInfo: (info: any) => void;
  explodeFactor: number;
  layerOpacity: number;
  showStrata: boolean;
  showBorehole: boolean;
  showFractures: boolean;
  showAquifers: boolean;
  showPredictions: boolean;
  showAxes: boolean;
}

// 3D Scene internal components
const GeologicalScene = ({
  logs,
  predictionDepthIndex,
  onSelectDepthIndex,
  setHoveredInfo,
  explodeFactor,
  layerOpacity,
  showStrata,
  showBorehole,
  showFractures,
  showAquifers,
  showPredictions,
  showAxes,
}: GeologicalSceneProps) => {
  if (logs.length === 0) return null;

  const totalDepth = logs[logs.length - 1].depth;
  
  // Scale factor: 1 meter = 0.15 units in ThreeJS space
  const SCALE_Y = 0.15;
  const BLOCK_WIDTH = 5;
  const BLOCK_LENGTH = 5;

  // Process logs into contiguous geological layers
  const layers: { rockType: string; start: number; end: number }[] = [];
  let currentLayer = { rockType: logs[0].rock_type, start: logs[0].depth, end: logs[0].depth };

  for (let i = 1; i < logs.length; i++) {
    const rec = logs[i];
    if (rec.rock_type === currentLayer.rockType) {
      currentLayer.end = rec.depth;
    } else {
      layers.push({ ...currentLayer });
      currentLayer = { rockType: rec.rock_type, start: rec.depth, end: rec.depth };
    }
  }
  layers.push({ ...currentLayer });

  // Helper to find exploded Y-axis offset for elements at a given depth
  const getExplodeOffset = (depth: number) => {
    const layerIdx = layers.findIndex((l) => depth >= l.start && depth <= l.end);
    if (layerIdx === -1) return 0;
    return layerIdx * explodeFactor;
  };

  // Expose fractures as discrete disks
  const fractures: { depth: number; index: number }[] = [];
  logs.forEach((rec, idx) => {
    if (rec.is_fractured && idx % 3 === 0) {
      fractures.push({ depth: rec.depth, index: idx });
    }
  });

  // Expose water-bearing segments as semi-transparent shells
  const waterSegments: { start: number; end: number }[] = [];
  let currentWater: any = null;
  logs.forEach((rec) => {
    if (rec.has_water) {
      if (!currentWater) {
        currentWater = { start: rec.depth, end: rec.depth };
      } else {
        currentWater.end = rec.depth;
      }
    } else {
      const cw = currentWater;
      if (cw) {
        waterSegments.push({ start: cw.start, end: cw.end });
        currentWater = null;
      }
    }
  });
  const cwFinal = currentWater;
  if (cwFinal) {
    waterSegments.push({ start: cwFinal.start, end: cwFinal.end });
  }

  // Expose AI prediction zones as highlights
  const predictionSegments: { start: number; end: number; confidence: number }[] = [];
  let currentPred: any = null;
  logs.forEach((rec) => {
    const isWater = rec.prediction !== undefined ? rec.prediction : rec.has_water;
    const conf = rec.confidence !== undefined ? rec.confidence : 0.85;

    if (isWater) {
      if (!currentPred) {
        currentPred = { start: rec.depth, end: rec.depth, sumConf: conf, count: 1 };
      } else {
        currentPred.end = rec.depth;
        currentPred.sumConf += conf;
        currentPred.count += 1;
      }
    } else {
      const cp = currentPred;
      if (cp) {
        predictionSegments.push({
          start: cp.start,
          end: cp.end,
          confidence: cp.sumConf / cp.count,
        });
        currentPred = null;
      }
    }
  });
  const cpFinal = currentPred;
  if (cpFinal) {
    predictionSegments.push({
      start: cpFinal.start,
      end: cpFinal.end,
      confidence: cpFinal.sumConf / cpFinal.count,
    });
  }

  return (
    <group position={[0, (totalDepth * SCALE_Y) / 2, 0]}>
      {/* 3D Geological Strata Blocks */}
      {showStrata && layers.map((layer, idx) => {
        const thickness = layer.end - layer.start;
        const height = thickness * SCALE_Y;
        // Shift Y-position based on starting depth plus the exploded spacer offset
        const centerY = -(layer.start + thickness / 2) * SCALE_Y - idx * explodeFactor;
        const color = ROCK_COLORS[layer.rockType] || ROCK_COLORS.Default;

        return (
          <mesh
            key={`layer-${idx}`}
            position={[0, centerY, 0]}
            onPointerOver={(e) => {
              e.stopPropagation();
              setHoveredInfo({
                type: "Stratum",
                title: `${layer.rockType} Layer`,
                depth: `${layer.start.toFixed(1)}m - ${layer.end.toFixed(1)}m`,
                details: `Thickness: ${thickness.toFixed(1)}m`,
              });
            }}
            onPointerOut={() => setHoveredInfo(null)}
          >
            <boxGeometry args={[BLOCK_WIDTH, height, BLOCK_LENGTH]} />
            <meshStandardMaterial
              color={color}
              transparent
              opacity={layerOpacity}
              roughness={0.7}
              metalness={0.1}
            />
            {/* Outline box wireframe to give an engineering layout look */}
            <lineSegments>
              <edgesGeometry args={[new THREE.BoxGeometry(BLOCK_WIDTH, height, BLOCK_LENGTH)]} />
              <lineBasicMaterial color="#94a3b8" linewidth={1} />
            </lineSegments>
          </mesh>
        );
      })}

      {/* Borehole Well Shaft cylinder */}
      {showBorehole && (
        <mesh
          position={[0, -(totalDepth * SCALE_Y) / 2, 0]}
          onPointerOver={(e) => {
            e.stopPropagation();
            setHoveredInfo({
              type: "Wellbore",
              title: "Borehole Shaft",
              depth: `0m - ${totalDepth.toFixed(1)}m`,
              details: "Standard exploration borehole diameter (150mm).",
            });
          }}
          onPointerOut={() => setHoveredInfo(null)}
        >
          <cylinderGeometry args={[0.08, 0.08, totalDepth * SCALE_Y, 16]} />
          <meshStandardMaterial color="#334155" roughness={0.3} metalness={0.8} />
        </mesh>
      )}

      {/* Fractures as inclined disks */}
      {showFractures && fractures.map((fracture, idx) => {
        const centerY = -fracture.depth * SCALE_Y - getExplodeOffset(fracture.depth);
        return (
          <mesh
            key={`fracture-${idx}`}
            position={[0, centerY, 0]}
            rotation={[Math.PI / 6, 0, 0]} // Fixed dip angle simulation for visual representation
            onPointerOver={(e) => {
              e.stopPropagation();
              setHoveredInfo({
                type: "Fracture",
                title: `Fracture Zone at ${fracture.depth}m`,
                depth: `${fracture.depth.toFixed(1)} meters`,
                details: "Angle: 30° dip, high secondary porosity.",
              });
            }}
            onPointerOut={() => setHoveredInfo(null)}
            onClick={() => onSelectDepthIndex(fracture.index)}
          >
            <cylinderGeometry args={[BLOCK_WIDTH / 2 - 0.1, BLOCK_WIDTH / 2 - 0.1, 0.04, 32]} />
            <meshBasicMaterial color="#f87171" transparent opacity={0.6} wireframe={false} />
          </mesh>
        );
      })}

      {/* Water bearing zone transparent volume */}
      {showAquifers && waterSegments.map((zone, idx) => {
        const thickness = zone.end - zone.start;
        const height = thickness * SCALE_Y;
        const centerY = -(zone.start + thickness / 2) * SCALE_Y - getExplodeOffset(zone.start + thickness / 2);

        return (
          <mesh key={`water-${idx}`} position={[0, centerY, 0]}>
            <cylinderGeometry args={[0.8, 0.8, height, 16]} />
            <meshStandardMaterial
              color="#0ea5e9"
              transparent
              opacity={0.3}
              roughness={0.1}
              metalness={0.1}
              side={THREE.DoubleSide}
            />
          </mesh>
        );
      })}

      {/* AI Prediction Highlight Overlay (Glowing Cyan Rings around borehole) */}
      {showPredictions && predictionSegments.map((seg, idx) => {
        const thickness = seg.end - seg.start;
        const height = thickness * SCALE_Y;
        const centerY = -(seg.start + thickness / 2) * SCALE_Y - getExplodeOffset(seg.start + thickness / 2);

        return (
          <mesh
            key={`pred-seg-${idx}`}
            position={[0, centerY, 0]}
            onPointerOver={(e) => {
              e.stopPropagation();
              setHoveredInfo({
                type: "AI Target",
                title: "Water Presence Target",
                depth: `${seg.start.toFixed(1)}m - ${seg.end.toFixed(1)}m`,
                details: `Confidence: ${(seg.confidence * 100).toFixed(1)}%`,
              });
            }}
            onPointerOut={() => setHoveredInfo(null)}
          >
            <cylinderGeometry args={[0.13, 0.13, height, 16]} />
            <meshBasicMaterial color="#06b6d4" transparent opacity={0.65} side={THREE.DoubleSide} />
          </mesh>
        );
      })}

      {/* Active prediction pointer (red arrow or sphere highlighting selected depth) */}
      {predictionDepthIndex !== null && logs[predictionDepthIndex] && (
        <mesh position={[0, -logs[predictionDepthIndex].depth * SCALE_Y - getExplodeOffset(logs[predictionDepthIndex].depth), 0]}>
          <sphereGeometry args={[0.18, 16, 16]} />
          <meshBasicMaterial color="#3b82f6" />
          <Html distanceFactor={8} position={[0.4, 0, 0]}>
            <div className="bg-white text-blue-600 text-xs px-2 py-1 rounded border border-blue-200 font-semibold shadow-lg whitespace-nowrap">
              Active: {logs[predictionDepthIndex].depth.toFixed(1)}m
            </div>
          </Html>
        </mesh>
      )}

      {/* Structural Grids at Base & Reference Axes */}
      <gridHelper args={[12, 12, "#64748b", "#e2e8f0"]} position={[0, -totalDepth * SCALE_Y - (layers.length * explodeFactor) - 0.2, 0]} />
      {showAxes && <axesHelper args={[3]} />}
    </group>
  );
};

export const Subsurface3DViewer = ({
  logs,
  predictionDepthIndex,
  onSelectDepthIndex,
}: Subsurface3DViewerProps) => {
  const [hoveredInfo, setHoveredInfo] = useState<any>(null);

  // Inspection controls state
  const [explodeFactor, setExplodeFactor] = useState(0);
  const [layerOpacity, setLayerOpacity] = useState(0.45);
  const [showStrata, setShowStrata] = useState(true);
  const [showBorehole, setShowBorehole] = useState(true);
  const [showFractures, setShowFractures] = useState(true);
  const [showAquifers, setShowAquifers] = useState(true);
  const [showPredictions, setShowPredictions] = useState(true);
  const [showAxes, setShowAxes] = useState(true);

  return (
    <div className="w-full h-full relative bg-slate-50 border border-slate-200 rounded-lg overflow-hidden flex flex-col shadow-sm">
      {/* Header toolbar */}
      <div className="px-4 py-3 bg-white border-b border-slate-200 flex justify-between items-center z-10">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Subsurface 3D Structural Column</h3>
          <p className="text-xs text-slate-400 font-sans">React Three Fiber (R3F) WebGL Rendering</p>
        </div>
        <div className="flex gap-2">
          {Object.keys(ROCK_COLORS).map((key) => {
            if (key === "Default") return null;
            return (
              <div key={key} className="flex items-center gap-1 text-[10px] text-slate-500 font-sans">
                <span
                  className="w-2.5 h-2.5 rounded-sm inline-block"
                  style={{ backgroundColor: ROCK_COLORS[key] }}
                />
                <span>{key}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* WebGL Canvas & Controls Sidebar Wrapper */}
      <div className="flex-1 relative flex">
        {/* Canvas Area */}
        <div className="flex-1 relative min-w-0">
          <Canvas camera={{ position: [6, 4, 8], fov: 45 }} className="w-full h-full">
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 20, 10]} intensity={0.8} castShadow />
            <directionalLight position={[-10, -5, -10]} intensity={0.3} />
            
            <GeologicalScene
              logs={logs}
              predictionDepthIndex={predictionDepthIndex}
              onSelectDepthIndex={onSelectDepthIndex}
              hoveredInfo={hoveredInfo}
              setHoveredInfo={setHoveredInfo}
              explodeFactor={explodeFactor}
              layerOpacity={layerOpacity}
              showStrata={showStrata}
              showBorehole={showBorehole}
              showFractures={showFractures}
              showAquifers={showAquifers}
              showPredictions={showPredictions}
              showAxes={showAxes}
            />

            <OrbitControls
              enableDamping
              dampingFactor={0.05}
              maxPolarAngle={Math.PI / 2}
              minDistance={2}
              maxDistance={25}
            />
          </Canvas>

          {/* Hover Inspector Tooltip overlay */}
          {hoveredInfo && (
            <div className="absolute bottom-4 left-4 bg-white/95 border border-slate-200 p-3 rounded shadow-lg font-sans text-xs text-slate-700 max-w-xs z-10 pointer-events-none">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">
                {hoveredInfo.type}
              </div>
              <div className="font-semibold text-slate-800 text-sm mb-1">{hoveredInfo.title}</div>
              <div className="flex justify-between border-t border-slate-150 pt-1.5 gap-4">
                <span className="text-slate-400">Interval:</span>
                <span className="text-slate-900 font-bold">{hoveredInfo.depth}</span>
              </div>
              <div className="mt-1 text-slate-500 leading-relaxed text-[11px]">
                {hoveredInfo.details}
              </div>
            </div>
          )}

          {/* Help controls indicator */}
          <div className="absolute top-4 right-4 bg-white/80 border border-slate-200 px-2.5 py-1 rounded text-[10px] text-slate-500 pointer-events-none font-sans">
            Drag to Rotate | Scroll to Zoom | Right-Click to Pan
          </div>
        </div>

        {/* CAD Controls Sidebar */}
        <div className="w-56 border-l border-slate-200 bg-white p-4 flex flex-col gap-4 overflow-y-auto text-slate-700 select-none">
          <div className="border-b border-slate-100 pb-2">
            <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">3D Model Inspector</h4>
            <p className="text-[9px] text-slate-400">Control visual segments and exploded spacing</p>
          </div>

          {/* Explode Slider */}
          <div className="space-y-1">
            <label className="text-[9px] font-bold text-slate-400 block uppercase">Explode Strata Spacing</label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="1.5"
                step="0.1"
                value={explodeFactor}
                onChange={(e) => setExplodeFactor(parseFloat(e.target.value))}
                className="flex-1 accent-blue-600 cursor-pointer h-1 bg-slate-100 rounded-lg appearance-none"
              />
              <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-50 border border-slate-200 px-1 rounded">{explodeFactor.toFixed(1)}x</span>
            </div>
          </div>

          {/* Opacity Slider */}
          <div className="space-y-1">
            <label className="text-[9px] font-bold text-slate-400 block uppercase">Strata Opacity</label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={layerOpacity}
                onChange={(e) => setLayerOpacity(parseFloat(e.target.value))}
                className="flex-1 accent-blue-600 cursor-pointer h-1 bg-slate-100 rounded-lg appearance-none"
              />
              <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-50 border border-slate-200 px-1 rounded">{(layerOpacity * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div className="border-t border-slate-100 my-1" />

          {/* Toggle Switches */}
          <div className="space-y-2.5">
            <label className="text-[9px] font-bold text-slate-400 block uppercase">Toggle Layers</label>
            
            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-[11px] text-slate-600 font-semibold group-hover:text-slate-800">Geological Strata</span>
              <input
                type="checkbox"
                checked={showStrata}
                onChange={(e) => setShowStrata(e.target.checked)}
                className="w-3.5 h-3.5 accent-blue-600 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-[11px] text-slate-600 font-semibold group-hover:text-slate-800">Wellbore Shaft</span>
              <input
                type="checkbox"
                checked={showBorehole}
                onChange={(e) => setShowBorehole(e.target.checked)}
                className="w-3.5 h-3.5 accent-blue-600 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-[11px] text-slate-600 font-semibold group-hover:text-slate-800">Fracture Zones</span>
              <input
                type="checkbox"
                checked={showFractures}
                onChange={(e) => setShowFractures(e.target.checked)}
                className="w-3.5 h-3.5 accent-blue-600 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-[11px] text-slate-600 font-semibold group-hover:text-slate-800">Groundwater Aquifers</span>
              <input
                type="checkbox"
                checked={showAquifers}
                onChange={(e) => setShowAquifers(e.target.checked)}
                className="w-3.5 h-3.5 accent-blue-600 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-[11px] text-slate-600 font-semibold group-hover:text-slate-800">AI Water Predictions</span>
              <input
                type="checkbox"
                checked={showPredictions}
                onChange={(e) => setShowPredictions(e.target.checked)}
                className="w-3.5 h-3.5 accent-blue-600 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between cursor-pointer group">
              <span className="text-[11px] text-slate-600 font-semibold group-hover:text-slate-800">Coordinate Axes</span>
              <input
                type="checkbox"
                checked={showAxes}
                onChange={(e) => setShowAxes(e.target.checked)}
                className="w-3.5 h-3.5 accent-blue-600 cursor-pointer"
              />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Subsurface3DViewer;
