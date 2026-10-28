import { Html, OrbitControls, PerspectiveCamera } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo, useState } from "react";
import * as THREE from "three";

import type { AssetItem } from "../types/api";

type GraphNode = AssetItem & { position: [number, number, number] };

function colorFor(type: string): string {
  if (type === "Domain") return "#22d3ee";
  if (type === "Host") return "#38bdf8";
  if (type === "Service") return "#8b5cf6";
  if (type === "TLS") return "#34d399";
  return "#f59e0b";
}

function sizeFor(type: string): number {
  if (type === "Domain") return 0.52;
  if (type === "Host") return 0.38;
  if (type === "Service") return 0.25;
  return 0.22;
}

function NodeObject({ node, onSelect }: { node: GraphNode; onSelect: (node: GraphNode) => void }) {
  const [hovered, setHovered] = useState(false);
  const color = colorFor(node.type);
  const size = sizeFor(node.type);

  return (
    <group position={node.position}>
      <mesh
        onClick={(event) => { event.stopPropagation(); onSelect(node); }}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.22 : 1}
      >
        <sphereGeometry args={[size, 28, 28]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={node.status === "Warning" ? 2.8 : 1.4} metalness={0.5} roughness={0.3} />
      </mesh>
      <Html distanceFactor={12} position={[0, size + 0.25, 0]} style={{ pointerEvents: "none" }}>
        <div className="rounded-md border border-slate-700/60 bg-slate-950/80 px-2 py-1 text-[10px] whitespace-nowrap text-slate-300 backdrop-blur">
          {node.name}
        </div>
      </Html>
    </group>
  );
}

function Connector({ start, end }: { start: [number, number, number]; end: [number, number, number] }) {
  const startVector = new THREE.Vector3(...start);
  const endVector = new THREE.Vector3(...end);
  const direction = endVector.clone().sub(startVector);
  const length = direction.length();
  const midpoint = startVector.clone().add(endVector).multiplyScalar(0.5);
  const quaternion = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
  return (
    <mesh position={midpoint} quaternion={quaternion}>
      <cylinderGeometry args={[0.01, 0.01, length, 8]} />
      <meshBasicMaterial color="#1e3a5f" transparent opacity={0.8} />
    </mesh>
  );
}

export default function AttackSurfaceScene({ assets }: { assets: AssetItem[] }) {
  const [selected, setSelected] = useState<GraphNode | null>(null);

  const nodes = useMemo<GraphNode[]>(() => {
    const source = assets.filter((asset) => ["Domain", "Host", "Service"].includes(asset.type)).slice(0, 42);
    return source.map((asset, index) => {
      const ring = asset.type === "Domain" ? 0 : asset.type === "Host" ? 1 : 2;
      const sameType = source.slice(0, index + 1).filter((item) => item.type === asset.type).length - 1;
      const total = ring === 0 ? 1 : ring === 1 ? Math.max(1, source.filter((item) => item.type === "Host").length) : Math.max(1, source.filter((item) => item.type === "Service").length);
      const angle = (sameType / Math.max(total, 1)) * Math.PI * 2;
      const radius = ring === 0 ? 0 : ring === 1 ? 2.6 : 4.2;
      return {
        ...asset,
        position: [Math.cos(angle) * radius, Math.sin(angle) * radius * 0.65, ring === 0 ? 0 : (sameType % 3) - 1] as [number, number, number],
      };
    });
  }, [assets]);

  const links = useMemo(() => {
    const domains = nodes.filter((node) => node.type === "Domain");
    const hosts = nodes.filter((node) => node.type === "Host");
    const services = nodes.filter((node) => node.type === "Service");
    const result: Array<[[number, number, number], [number, number, number]]> = [];
    domains.forEach((domain) => hosts.slice(0, 12).forEach((host) => result.push([domain.position, host.position])));
    services.forEach((service, index) => {
      const host = hosts[index % Math.max(hosts.length, 1)];
      if (host) result.push([host.position, service.position]);
    });
    return result.slice(0, 70);
  }, [nodes]);

  return (
    <div className="relative h-full w-full">
      <Canvas>
        <color attach="background" args={["#020617"]} />
        <PerspectiveCamera makeDefault position={[0, 0.5, 11]} fov={48} />
        <ambientLight intensity={0.45} />
        <pointLight position={[0, 3, 5]} intensity={32} color="#22d3ee" />
        <pointLight position={[-5, -2, 3]} intensity={18} color="#8b5cf6" />
        {links.map((link, index) => <Connector key={index} start={link[0]} end={link[1]} />)}
        {nodes.map((node) => <NodeObject key={node.id} node={node} onSelect={setSelected} />)}
        <OrbitControls enablePan enableZoom enableRotate minDistance={5} maxDistance={18} />
      </Canvas>

      {selected ? (
        <div className="absolute right-5 top-5 w-[290px] rounded-2xl border border-slate-700 bg-slate-950/92 p-5 shadow-2xl backdrop-blur-xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-400">Selected Asset</p>
              <p className="mt-2 text-sm font-semibold text-white">{selected.name}</p>
            </div>
            <button className="text-slate-500 hover:text-white" onClick={() => setSelected(null)} aria-label="Close">×</button>
          </div>
          <div className="mt-5 space-y-3 text-xs">
            <div className="flex justify-between gap-4"><span className="text-slate-600">Type</span><span className="text-slate-300">{selected.type}</span></div>
            <div className="flex justify-between gap-4"><span className="text-slate-600">Address</span><span className="max-w-40 text-right text-slate-300">{selected.address}</span></div>
            <div className="flex justify-between gap-4"><span className="text-slate-600">Status</span><span className="text-emerald-300">{selected.status}</span></div>
            <div className="border-t border-slate-800 pt-3 text-slate-500">{selected.details}</div>
          </div>
        </div>
      ) : null}

      {assets.length === 0 ? (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-slate-600">No inventory data available yet.</div>
      ) : null}
    </div>
  );
}
