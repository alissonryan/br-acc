import { useCallback, useRef, useState } from "react";
import ForceGraph2D, {
  type ForceGraphMethods,
  type LinkObject,
  type NodeObject,
} from "react-force-graph-2d";

import type { GraphData } from "@/api/client";
import { type EntityType, entityColors } from "@/styles/tokens";

import { EdgeDetail } from "./EdgeDetail";
import styles from "./GraphCanvas.module.css";

interface GraphCanvasProps {
  data: GraphData;
  centerId: string;
  enabledTypes: Set<string>;
  onNodeClick: (nodeId: string) => void;
}

interface GraphNodeObject extends NodeObject {
  id: string;
  label: string;
  type: string;
  connectionCount?: number;
}

interface GraphLinkObject extends LinkObject {
  type: string;
  confidence?: number;
  value?: number;
  properties: Record<string, unknown>;
}

export function GraphCanvas({ data, centerId, enabledTypes, onNodeClick }: GraphCanvasProps) {
  const fgRef = useRef<ForceGraphMethods<GraphNodeObject, GraphLinkObject> | undefined>(undefined);
  const [selectedEdge, setSelectedEdge] = useState<GraphLinkObject | null>(null);

  const filteredNodes = data.nodes.filter((n) => enabledTypes.has(n.type));
  const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));
  const filteredEdges = data.edges.filter(
    (e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target),
  );

  const connectionCounts = new Map<string, number>();
  for (const edge of filteredEdges) {
    connectionCounts.set(edge.source, (connectionCounts.get(edge.source) ?? 0) + 1);
    connectionCounts.set(edge.target, (connectionCounts.get(edge.target) ?? 0) + 1);
  }

  const graphData = {
    nodes: filteredNodes.map((n) => ({
      ...n,
      connectionCount: connectionCounts.get(n.id) ?? 0,
    })),
    links: filteredEdges.map((e) => ({
      source: e.source,
      target: e.target,
      type: e.type,
      confidence: e.confidence,
      value: (e.properties as Record<string, unknown>)?.value as number | undefined,
      properties: e.properties,
    })),
  };

  const nodeColor = useCallback((node: GraphNodeObject) => {
    return entityColors[node.type as EntityType] ?? "#555";
  }, []);

  const nodeSize = useCallback((node: GraphNodeObject) => {
    if (node.id === centerId) return 8;
    const count = node.connectionCount ?? 0;
    return Math.max(3, Math.min(6, 3 + count * 0.5));
  }, [centerId]);

  const nodeLabel = useCallback((node: GraphNodeObject) => {
    return node.label;
  }, []);

  const linkColor = useCallback((_link: GraphLinkObject) => {
    return "rgba(255, 255, 255, 0.12)";
  }, []);

  const linkWidth = useCallback((link: GraphLinkObject) => {
    const value = link.value ?? 0;
    const confidence = link.confidence ?? 1;
    const baseWidth = confidence >= 0.9 ? 1.5 : 0.5;
    if (value > 0) {
      return baseWidth + Math.min(4, Math.log10(value + 1) * 0.5);
    }
    return baseWidth;
  }, []);

  const linkLineDash = useCallback((link: GraphLinkObject) => {
    const confidence = link.confidence ?? 1;
    return confidence < 0.9 ? [4, 2] : null;
  }, []);

  const handleNodeClick = useCallback(
    (node: GraphNodeObject) => {
      onNodeClick(node.id);
    },
    [onNodeClick],
  );

  const handleLinkClick = useCallback((link: GraphLinkObject) => {
    setSelectedEdge(link);
  }, []);

  const handleCloseEdgeDetail = useCallback(() => {
    setSelectedEdge(null);
  }, []);

  return (
    <div className={styles.canvas}>
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeColor={nodeColor}
        nodeVal={nodeSize}
        nodeLabel={nodeLabel}
        linkColor={linkColor}
        linkWidth={linkWidth}
        linkLineDash={linkLineDash}
        onNodeClick={handleNodeClick}
        onLinkClick={handleLinkClick}
        backgroundColor="#0d100e"
        linkDirectionalParticles={0}
        cooldownTicks={100}
        nodeCanvasObjectMode={() => "after" as const}
        nodeCanvasObject={(node: GraphNodeObject, ctx: CanvasRenderingContext2D) => {
          if (!node.x || !node.y) return;
          const label = node.label;
          const fontSize = node.id === centerId ? 4 : 3;
          ctx.font = `${fontSize}px monospace`;
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
          ctx.fillText(label, node.x, node.y + 5);
        }}
      />
      {selectedEdge && (
        <EdgeDetail edge={selectedEdge} onClose={handleCloseEdgeDetail} />
      )}
    </div>
  );
}
